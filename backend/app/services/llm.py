"""LLM service using LiteLLM for model-agnostic AI integration."""

import os
import datetime
from collections.abc import AsyncGenerator

from litellm import acompletion, token_counter

from app.config.logging import get_logger
from app.config.settings import settings
from app.schemas.chat import LLMMessage, LLMStreamChunk

logger = get_logger(__name__)

# System prompts for different modes
SOCRATIC_SYSTEM_PROMPT = """You are a Socratic tutor helping a programmer solve coding problems through guided discovery.

CRITICAL - READ THE USER'S MESSAGES CAREFULLY:
- Before asking a question, check if the user has ALREADY answered it in their previous messages
- If the user already explained something, acknowledge it and move to the NEXT topic
- Do NOT ask about things the user has already explained

RULES:
- NEVER give direct answers or show complete solutions
- Ask guiding questions that lead the user to insights
- If user is stuck, give progressively more specific hints
- Always respond in Markdown format
- Use code blocks for code examples (but only fragments, never full solutions)
- Be professional and concise - avoid excessive praise or filler phrases
- NEVER repeat or rephrase questions the user has already answered

PROGRESSION:
- Progress through stages: problem understanding → data structure choice → algorithm steps → edge cases → complexity → implementation
- When the user explains their approach correctly, say "Good, you've got the approach" and move to the NEXT stage (e.g., edge cases or complexity)
- If they've covered the algorithm fully, ask them to implement it in code
- Do NOT keep asking them to elaborate on things they've already explained

APPROACH:
1. Read the user's message carefully - what have they already figured out?
2. Acknowledge what they got right in ONE short sentence
3. Ask ONE question about something they HAVEN'T addressed yet
4. If they've addressed everything, tell them to start coding

Remember: Your goal is to help them learn, not to endlessly quiz them on things they already understand."""

DIRECT_SYSTEM_PROMPT = """You are a programming assistant for a coding practice platform.

CRITICAL - BE DIRECT, NOT SOCRATIC:
- Do NOT ask the user questions - give them answers
- Do NOT ask them to elaborate or explain more - just show them the solution
- If they describe an approach, confirm if it's correct and SHOW the code implementation
- Your job is to TEACH by SHOWING, not by questioning

RULES:
- Give clear, direct explanations with code examples
- SHOW complete solutions when the user asks or describes their approach
- Explain bugs and errors directly with fixes
- Always respond in Markdown format
- Use proper code blocks with syntax highlighting
- Be concise - get to the point quickly without filler phrases

APPROACH:
1. If user describes an approach: confirm it's correct and show the implementation
2. If user asks a question: answer it directly with code examples
3. If user has a bug: show exactly what's wrong and how to fix it
4. Always provide working code, not questions

Remember: You are here to GIVE direct feedback. Show, don't quiz."""


def get_available_models() -> list[str]:
    """
    Get list of available LLM models based on configured API keys.

    Returns:
        List of available model names from settings
    """
    supported = settings.llm_supported_models.split(",")
    available = []

    for model in supported:
        model = model.strip()
        # Check if required API key is configured
        if model.startswith("gemini/") and settings.google_api_key:
            available.append(model)
        elif model.startswith("gpt-") and settings.openai_api_key:
            available.append(model)
        elif model.startswith("claude-") and settings.anthropic_api_key:
            available.append(model)
        elif "/" not in model:  # Assume OpenAI if no prefix
            if settings.openai_api_key:
                available.append(model)

    if not available:
        logger.warning("no_llm_models_available", supported=supported)

    return available


def get_default_model() -> str:
    """Get the default LLM model (first available model)."""
    available = get_available_models()
    if not available:
        raise ValueError("No LLM models available - check API key configuration")
    return available[0]


def set_api_keys():
    """Set API keys as environment variables for LiteLLM."""
    if settings.google_api_key:
        # Set both for compatibility with different LiteLLM model prefixes
        os.environ["GEMINI_API_KEY"] = settings.google_api_key
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


def build_context_message(
    problem_title: str,
    problem_description: str,
    problem_constraints: list[str],
    problem_examples: list[dict],
    current_code: str | None = None,
    test_results: dict | None = None,
) -> str:
    """
    Build context message from problem data and user state.

    Args:
        problem_title: Title of the problem
        problem_description: Problem description
        problem_constraints: List of constraint strings
        problem_examples: List of example dicts (input/output/explanation)
        current_code: User's current code (optional)
        test_results: Test execution results (optional)

    Returns:
        Formatted context string
    """
    context = f"""## Problem: {problem_title}

{problem_description}

**Constraints:**
"""
    for constraint in problem_constraints:
        context += f"- {constraint}\n"

    context += "\n**Examples:**\n"
    for i, example in enumerate(problem_examples, 1):
        context += f"\nExample {i}:\n"
        context += f"- Input: `{example.get('input', '')}`\n"
        context += f"- Output: `{example.get('output', '')}`\n"
        if example.get('explanation'):
            context += f"- Explanation: {example['explanation']}\n"

    if current_code:
        # Truncate code if too long (keep first 2000 and last 500 chars)
        if len(current_code) > 3000:
            code_truncated = current_code[:2000] + "\n\n... [code truncated] ...\n\n" + current_code[-500:]
        else:
            code_truncated = current_code

        context += f"\n\n**Current Code:**\n```python\n{code_truncated}\n```\n"

    if test_results:
        context += "\n**Latest Test Results:**\n"
        passed = test_results.get("passed", False)
        context += f"- Status: {'✅ Passed' if passed else '❌ Failed'}\n"

        if not passed:
            if "error" in test_results:
                context += f"- Error: {test_results['error']}\n"
            if "failed_test" in test_results:
                failed = test_results["failed_test"]
                context += f"- Failed on test case {failed.get('number', '?')}\n"
                context += f"  - Input: `{failed.get('input')}`\n"
                context += f"  - Expected: `{failed.get('expected')}`\n"
                context += f"  - Got: `{failed.get('output')}`\n"

    return context


async def stream_chat_completion(
    messages: list[LLMMessage],
    model: str | None = None,
    mode: str = "socratic",
) -> AsyncGenerator[LLMStreamChunk, None]:
    """
    Stream chat completion from LLM.

    Args:
        messages: List of LLM messages (system, user, assistant)
        model: LLM model to use (uses default if None)
        mode: Chat mode ('socratic' or 'direct')

    Yields:
        LLMStreamChunk objects with content and finish_reason

    Raises:
        ValueError: If no models available or invalid model
        Exception: LLM API errors
    """
    set_api_keys()

    if model is None:
        model = get_default_model()

    # Validate model is available
    available = get_available_models()
    if model not in available:
        raise ValueError(f"Model {model} not available. Available: {available}")

    # Add system prompt based on mode
    system_prompt = SOCRATIC_SYSTEM_PROMPT if mode == "socratic" else DIRECT_SYSTEM_PROMPT

    # Build full message list with system prompt
    full_messages = [
        {"role": "system", "content": system_prompt}
    ] + [{"role": msg.role, "content": msg.content} for msg in messages]

    # Count tokens (for logging)
    try:
        total_tokens = token_counter(model=model, messages=full_messages)
        logger.info("llm_request", model=model, mode=mode, tokens=total_tokens, message_count=len(messages))
    except Exception as e:
        logger.warning("token_count_failed", error=str(e))

    try:
        # Stream completion
        response = await acompletion(
            model=model,
            messages=full_messages,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                finish_reason = chunk.choices[0].finish_reason

                if hasattr(delta, "content") and delta.content:
                    yield LLMStreamChunk(content=delta.content, finish_reason=finish_reason)
                elif finish_reason:
                    yield LLMStreamChunk(content="", finish_reason=finish_reason)

        logger.info("llm_stream_completed", model=model)

    except Exception as e:
        logger.error("llm_stream_error", model=model, error=str(e))
        raise


async def generate_session_title(first_message: str) -> str:
    """
    Generate a short title for a chat session from the first user message.

    Uses a fast, cheap model (gemini-flash) regardless of session model.
    Falls back to timestamp-based title on error.

    Args:
        first_message: The first user message in the session

    Returns:
        Generated title (max 50 chars) or fallback
    """
    set_api_keys()

    # Use gemini-flash if available, otherwise first available model
    available = get_available_models()
    if not available:
        return f"Chat {datetime.now().strftime('%H:%M')}"

    model = "gemini/gemini-1.5-flash" if "gemini/gemini-1.5-flash" in available else available[0]

    try:
        response = await acompletion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "Generate a 3-5 word title for this conversation. Be concise and descriptive. Only return the title, nothing else."
                },
                {
                    "role": "user",
                    "content": f"Generate title for: {first_message[:200]}"
                }
            ],
            max_tokens=20,
            temperature=0.5,
            stream=False,
        )

        title = response.choices[0].message.content.strip()
        # Remove quotes if present
        title = title.strip('"').strip("'")
        # Truncate to 50 chars
        if len(title) > 50:
            title = title[:47] + "..."

        logger.info("session_title_generated", title=title)
        return title

    except Exception as e:
        logger.warning("title_generation_failed", error=str(e))
        from datetime import datetime
        return f"Chat {datetime.now().strftime('%H:%M')}"
