"""Judge0 client for code execution."""

import httpx

from app.config.logging import get_logger
from app.config.settings import settings

logger = get_logger(__name__)

# Language IDs for Judge0
LANGUAGE_MAP = {
    "python": 71,  # Python 3
    "javascript": 63,  # JavaScript (Node.js)
}


class Judge0Service:
    """Service for interacting with Judge0 CE (self-hosted or hosted)."""

    def __init__(self):
        """Initialize Judge0 client with endpoint and optional API key."""
        self.base_url = settings.judge0_url
        self.api_key = settings.judge0_api_key
        self._headers = {}
        if self.api_key:
            # Support both X-Auth-Token (self-hosted) and X-RapidAPI-Key (RapidAPI)
            self._headers["X-Auth-Token"] = self.api_key
        logger.info("judge0_initialized", endpoint=self.base_url, has_api_key=bool(self.api_key))

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
        language_id = LANGUAGE_MAP.get(language.lower())
        if not language_id:
            raise ValueError(f"Unsupported language: {language}")

        logger.info(
            "judge0_execute",
            language=language,
            code_length=len(source_code),
            has_stdin=bool(stdin),
        )

        # Submit to Judge0 with wait=true
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/submissions?base64_encoded=false&wait=true",
                headers=self._headers,
                json={
                    "source_code": source_code,
                    "language_id": language_id,
                    "stdin": stdin if stdin else None,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()

        logger.info(
            "judge0_completed",
            token=result.get("token"),
            status=result.get("status", {}).get("description"),
            time=result.get("time"),
        )

        return result

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
        language_id = LANGUAGE_MAP.get(language.lower())
        if not language_id:
            raise ValueError(f"Unsupported language: {language}")

        logger.info(
            "judge0_test_cases",
            language=language,
            test_count=len(test_cases),
        )

        # Execute each test case
        results = []
        with httpx.Client() as client:
            for i, (stdin_data, expected_output) in enumerate(test_cases, 1):
                response = client.post(
                    f"{self.base_url}/submissions?base64_encoded=false&wait=true",
                    headers=self._headers,
                    json={
                        "source_code": source_code,
                        "language_id": language_id,
                        "stdin": stdin_data,
                        "expected_output": expected_output,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()

                # Status ID 3 = Accepted
                passed = result.get("status", {}).get("id") == 3

                results.append({
                    "test_number": i,
                    "passed": passed,
                    "stdout": result.get("stdout"),
                    "stderr": result.get("stderr"),
                    "status": result.get("status", {}).get("description"),
                    "time": result.get("time"),
                    "memory": result.get("memory"),
                })

        logger.info(
            "judge0_test_cases_completed",
            passed=sum(1 for r in results if r["passed"]),
            total=len(results)
        )

        return results


# Global service instance
_service: Judge0Service | None = None


def get_judge0_service() -> Judge0Service:
    """Get or create Judge0 service singleton."""
    global _service
    if _service is None:
        _service = Judge0Service()
    return _service
