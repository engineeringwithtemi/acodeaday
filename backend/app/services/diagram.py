"""Service for generating pseudocode flowchart diagrams using LLM."""

import json

from litellm import acompletion

from app.config.logging import get_logger
from app.schemas.diagram import PseudocodeDiagramResponse
from app.services.llm import get_default_model, set_api_keys

logger = get_logger(__name__)

PSEUDOCODE_SYSTEM_PROMPT = """You are a code analysis tool that converts source code into a pseudocode flowchart.

Your task: Given source code, produce a JSON object with `nodes` and `edges` that represents the code's logic as a pseudocode flowchart.

RULES:
1. Convert code logic into plain-English pseudocode steps (NOT the original code syntax).
2. Each node has: id (string, e.g. "n0", "n1"), label (string, the pseudocode text), shape (string).
3. Each edge has: from (string, source node id), to (string, target node id), label (string or null).
4. Shape values MUST be one of: "rect", "diamond", "stadium", "subroutine", "circle"
   - "stadium" for Start and End nodes
   - "diamond" for conditional checks (if/else, while conditions, for-each loops)
   - "rect" for regular statements and operations
   - "subroutine" for function/method definitions
   - "circle" for loop-back connectors
5. Always start with a Start node (stadium) and end with an End node (stadium).
6. Keep labels concise (max ~40 chars). Use plain English, not code.
7. For conditionals: use "Yes"/"No" edge labels from diamond nodes.
8. For loops: show the loop condition as a diamond, body as rects, a circle connector back to the condition, and "done" as the exit edge label.
9. Aim for 5-20 nodes. Summarize repetitive logic; don't create a node for every line.
10. Return ONLY valid JSON matching the schema. No markdown, no explanation, no code fences.

Example — for a function that searches an array with a hash map:
{"nodes":[{"id":"n0","label":"Start","shape":"stadium"},{"id":"n1","label":"searchArray","shape":"subroutine"},{"id":"n2","label":"Initialize empty hash map","shape":"rect"},{"id":"n3","label":"For each element in array","shape":"diamond"},{"id":"n4","label":"Is element already in map?","shape":"diamond"},{"id":"n5","label":"Return found pair","shape":"rect"},{"id":"n6","label":"Add element to map","shape":"rect"},{"id":"n7","label":"Loop back","shape":"circle"},{"id":"n8","label":"Return not found","shape":"rect"},{"id":"n9","label":"End","shape":"stadium"}],"edges":[{"from":"n0","to":"n1","label":null},{"from":"n1","to":"n2","label":null},{"from":"n2","to":"n3","label":null},{"from":"n3","to":"n4","label":"Yes"},{"from":"n3","to":"n8","label":"done"},{"from":"n4","to":"n5","label":"Yes"},{"from":"n4","to":"n6","label":"No"},{"from":"n5","to":"n9","label":null},{"from":"n6","to":"n7","label":null},{"from":"n7","to":"n3","label":null},{"from":"n8","to":"n9","label":null}]}"""


async def generate_pseudocode_diagram(code: str, language: str) -> PseudocodeDiagramResponse:
    """Generate a pseudocode flowchart from user code using LLM.

    Args:
        code: The user's source code
        language: Programming language ("python" or "javascript")

    Returns:
        PseudocodeDiagramResponse with nodes and edges

    Raises:
        ValueError: If LLM response is not valid JSON or fails schema validation
        TimeoutError: If LLM call times out
    """
    set_api_keys()
    model = get_default_model()

    # Smart truncation: keep first 2000 + last 500 chars if code is too long
    if len(code) > 2500:
        truncated_code = code[:2000] + "\n# ... (truncated) ...\n" + code[-500:]
    else:
        truncated_code = code

    user_message = f"Language: {language}\n\nCode:\n```{language}\n{truncated_code}\n```"

    logger.info(
        "pseudocode_diagram_request",
        model=model,
        language=language,
        code_length=len(code),
    )

    response = await acompletion(
        model=model,
        messages=[
            {"role": "system", "content": PSEUDOCODE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "PseudocodeDiagram",
                "schema": PseudocodeDiagramResponse.model_json_schema(),
            },
        },
        max_tokens=2048,
        temperature=0.3,
        timeout=30,
        stream=False,
    )

    raw_content = response.choices[0].message.content.strip()

    # Strip markdown code fences if LLM wraps output despite instructions
    if raw_content.startswith("```"):
        lines = raw_content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_content = "\n".join(lines).strip()

    # Parse and validate with Pydantic
    try:
        raw_data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error(
            "pseudocode_diagram_json_error",
            error=str(e),
            raw=raw_content[:200],
        )
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    result = PseudocodeDiagramResponse.model_validate(raw_data)

    logger.info(
        "pseudocode_diagram_generated",
        model=model,
        node_count=len(result.nodes),
        edge_count=len(result.edges),
    )

    return result
