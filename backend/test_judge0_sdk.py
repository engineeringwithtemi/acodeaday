"""Test Judge0 SDK integration."""

from app.services.judge0 import get_judge0_service


def test_basic_execution():
    """Test basic code execution."""
    print("Testing Judge0 SDK basic execution...")

    service = get_judge0_service()

    # Simple print test
    result = service.execute_code(
        source_code='print("Hello from Judge0 SDK!")',
        language="python"
    )

    print(f"Status: {result['status']}")
    print(f"Stdout: {result['stdout']}")
    print(f"Stderr: {result['stderr']}")
    print(f"Time: {result['time']}")
    print(f"Memory: {result['memory']}")


def test_with_test_cases():
    """Test execution with multiple test cases."""
    print("\nTesting Judge0 SDK with test cases...")

    service = get_judge0_service()

    # Code that reads input and echoes it
    code = 'print(input())'

    test_cases = [
        ("Hello", "Hello"),
        ("World", "World"),
        ("Python", "Python"),
    ]

    results = service.execute_with_test_cases(
        source_code=code,
        language="python",
        test_cases=test_cases
    )

    print(f"\nTest Results:")
    for r in results:
        status = "✓" if r["passed"] else "✗"
        print(f"  {status} Test {r['test_number']}: {r['status']}")
        print(f"     stdout: {r['stdout']}")


if __name__ == "__main__":
    test_basic_execution()
    test_with_test_cases()
