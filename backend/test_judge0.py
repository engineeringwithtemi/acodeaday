"""Quick test script for Judge0 integration."""

import asyncio

from app.services.judge0 import get_judge0_client
from app.services.wrapper import (
    generate_python_wrapper,
    get_execution_summary,
    parse_judge0_output,
)


async def test_judge0_basic():
    """Test basic Judge0 connectivity."""
    print("Testing Judge0 basic execution...")

    client = get_judge0_client()

    # Simple Hello World test
    code = 'print("Hello from Judge0!")'

    result = await client.execute_code(code, "python")

    print(f"Status: {result['status']['description']}")
    print(f"Stdout: {result['stdout']}")
    print(f"Stderr: {result['stderr']}")
    print(f"Time: {result['time']}s")
    print(f"Memory: {result['memory']} KB")

    await client.close()


async def test_judge0_with_wrapper():
    """Test Judge0 with test wrapper."""
    print("\nTesting Judge0 with wrapper...")

    client = get_judge0_client()

    # Simulate user code (Two Sum solution)
    user_code = '''from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        hashmap = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in hashmap:
                return [hashmap[complement], i]
            hashmap[num] = i
        return []
'''

    # Create mock test cases
    class MockTestCase:
        def __init__(self, input_data, expected, is_hidden=False):
            self.input = input_data
            self.expected = expected
            self.is_hidden = is_hidden

    test_cases = [
        MockTestCase([[2, 7, 11, 15], 9], [0, 1], False),
        MockTestCase([[3, 2, 4], 6], [1, 2], False),
        MockTestCase([[3, 3], 6], [0, 1], True),
    ]

    # Generate wrapper
    wrapped_code = generate_python_wrapper(user_code, test_cases, "twoSum")

    print("Generated wrapper code:")
    print("=" * 60)
    print(wrapped_code)
    print("=" * 60)

    # Execute on Judge0
    result = await client.execute_code(wrapped_code, "python")

    print(f"\nStatus: {result['status']['description']}")
    print(f"Stdout: {result['stdout']}")

    # Parse results
    if result["stdout"]:
        test_results = parse_judge0_output(result["stdout"])
        summary = get_execution_summary(test_results)

        print(f"\nTest Results:")
        for r in test_results:
            status = "✓" if r["passed"] else "✗"
            hidden = " (hidden)" if r["is_hidden"] else ""
            print(
                f"  {status} Test {r['test_number']}{hidden}: "
                f"output={r.get('output')}, expected={r['expected']}"
            )

        print(f"\nSummary: {summary['passed']}/{summary['total']} passed")

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_judge0_basic())
    asyncio.run(test_judge0_with_wrapper())
