"""Judge0 client for code execution using official SDK."""

from judge0 import LanguageAlias, TestCase
from judge0.api import wait
from judge0.clients import Client
from judge0.submission import Submission

from app.config.logging import get_logger
from app.config.settings import settings

logger = get_logger(__name__)

# Language mapping from our enum to Judge0 LanguageAlias
LANGUAGE_MAP = {
    "python": LanguageAlias.PYTHON,  # Python 3
    "javascript": LanguageAlias.JAVASCRIPT,  # JavaScript (Node.js)
}


class Judge0Service:
    """Service for interacting with self-hosted Judge0 CE."""

    def __init__(self):
        """Initialize Judge0 client with self-hosted endpoint."""
        self.client = Client(endpoint=settings.judge0_url)
        logger.info("judge0_initialized", endpoint=settings.judge0_url)

    def execute_code(
        self, source_code: str, language: str, stdin: str = ""
    ) -> dict:
        """
        Execute code on Judge0 and return results.

        Args:
            source_code: Code to execute
            language: Programming language ("python" or "javascript")
            stdin: Standard input to pass to the program

        Returns:
            Dict with execution results

        Example:
            service = Judge0Service()
            result = service.execute_code(
                source_code="print('Hello')",
                language="python"
            )
            print(result["stdout"])  # "Hello\\n"
        """
        judge0_language = LANGUAGE_MAP.get(language.lower())
        if not judge0_language:
            raise ValueError(f"Unsupported language: {language}")

        logger.info(
            "judge0_execute",
            language=language,
            code_length=len(source_code),
            has_stdin=bool(stdin),
        )

        # Create submission object
        submission = Submission(
            source_code=source_code,
            language=judge0_language,
            stdin=stdin,
        )

        # Execute using judge0 SDK
        submission = self.client.create_submission(submission)

        # Wait for completion
        submission = wait(client=self.client, submissions=submission)

        logger.info(
            "judge0_completed",
            token=submission.token,
            status=submission.status.description if submission.status else None,
            time=submission.time,
        )

        # Convert to dict for easier handling
        return {
            "token": submission.token,
            "status": {
                "id": submission.status.id if submission.status else None,
                "description": submission.status.description if submission.status else None,
            },
            "stdout": submission.stdout,
            "stderr": submission.stderr,
            "compile_output": submission.compile_output,
            "message": submission.message,
            "time": submission.time,
            "memory": submission.memory,
        }

    def execute_with_test_cases(
        self, source_code: str, language: str, test_cases: list[tuple[str, str]]
    ) -> list[dict]:
        """
        Execute code with multiple test cases.

        Args:
            source_code: Code to execute
            language: Programming language
            test_cases: List of (input, expected_output) tuples

        Returns:
            List of test results

        Example:
            results = service.execute_with_test_cases(
                source_code="print(input())",
                language="python",
                test_cases=[("Hello", "Hello"), ("World", "World")]
            )
        """
        judge0_language = LANGUAGE_MAP.get(language.lower())
        if not judge0_language:
            raise ValueError(f"Unsupported language: {language}")

        # Convert to Judge0 TestCase objects
        judge0_test_cases = [
            TestCase(stdin=inp, expected_output=exp) for inp, exp in test_cases
        ]

        logger.info(
            "judge0_test_cases",
            language=language,
            test_count=len(judge0_test_cases),
        )

        # Create submission object with test cases
        submission = Submission(
            source_code=source_code,
            language=judge0_language,
            test_cases=judge0_test_cases,
        )

        # Execute with test cases
        submissions = self.client.create_submission(submission)

        # Wait for all to complete
        submissions = wait(client=self.client, submissions=submissions)

        # Convert results to dicts
        results = []
        if isinstance(submissions, list):
            for i, sub in enumerate(submissions):
                results.append({
                    "test_number": i + 1,
                    "passed": sub.status.id == 3 if sub.status else False,  # 3 = Accepted
                    "stdout": sub.stdout,
                    "stderr": sub.stderr,
                    "status": sub.status.description if sub.status else None,
                    "time": sub.time,
                    "memory": sub.memory,
                })
        else:
            # Single submission
            results.append({
                "test_number": 1,
                "passed": submissions.status.id == 3 if submissions.status else False,
                "stdout": submissions.stdout,
                "stderr": submissions.stderr,
                "status": submissions.status.description if submissions.status else None,
                "time": submissions.time,
                "memory": submissions.memory,
            })

        logger.info("judge0_test_cases_completed", passed=sum(1 for r in results if r["passed"]), total=len(results))

        return results


# Global service instance
_service: Judge0Service | None = None


def get_judge0_service() -> Judge0Service:
    """Get or create Judge0 service singleton."""
    global _service
    if _service is None:
        _service = Judge0Service()
    return _service
