#!/usr/bin/env python3
"""Script to add leetcode_no field to all problem YAML files."""

import re
from pathlib import Path

# Mapping of problem titles to LeetCode numbers
# Source: https://leetcode.com/problemset/
LEETCODE_MAPPING = {
    "Two Sum": 1,
    "Add Two Numbers": 2,
    "Longest Substring Without Repeating Characters": 3,
    "Median of Two Sorted Arrays": 4,
    "Longest Palindromic Substring": 5,
    "Reverse Integer": 7,
    "Regular Expression Matching": 10,
    "Container With Most Water": 11,
    "3Sum": 15,
    "Letter Combinations of a Phone Number": 17,
    "Valid Parentheses": 20,
    "Merge Two Sorted Lists": 21,
    "Generate Parentheses": 22,
    "Merge K Sorted Lists": 23,
    "Reverse Nodes in K-Group": 25,
    "Remove Nth Node From End of List": 19,
    "Search in Rotated Sorted Array": 33,
    "Find Minimum in Rotated Sorted Array": 153,
    "Trapping Rain Water": 42,
    "Rotate Image": 48,
    "Group Anagrams": 49,
    "Pow(x, n)": 50,
    "Maximum Subarray": 53,
    "Jump Game": 55,
    "Merge Intervals": 56,
    "Insert Interval": 57,
    "Spiral Matrix": 54,
    "Jump Game II": 45,
    "Unique Paths": 62,
    "Unique Paths II": 63,
    "Min Cost Climbing Stairs": 746,
    "Climbing Stairs": 70,
    "Set Matrix Zeroes": 73,
    "Search a 2D Matrix": 74,
    "Word Search": 79,
    "Largest Rectangle in Histogram": 84,
    "Same Tree": 100,
    "Binary Tree Level Order Traversal": 102,
    "Maximum Depth of Binary Tree": 104,
    "Construct Binary Tree from Preorder and Inorder Traversal": 105,
    "Binary Tree Maximum Path Sum": 124,
    "Best Time to Buy and Sell Stock": 121,
    "Best Time to Buy and Sell Stock with Cooldown": 309,
    "Valid Palindrome": 125,
    "Clone Graph": 133,
    "Gas Station": 134,
    "Single Number": 136,
    "Word Break": 139,
    "Linked List Cycle": 141,
    "Reorder List": 143,
    "LRU Cache": 146,
    "Min Stack": 155,
    "Evaluate Reverse Polish Notation": 150,
    "Reverse Linked List": 206,
    "Course Schedule": 207,
    "Course Schedule II": 210,
    "Implement Trie (Prefix Tree)": 208,
    "Design Add and Search Words Data Structure": 211,
    "Word Search II": 212,
    "House Robber": 198,
    "House Robber II": 213,
    "Kth Largest Element in an Array": 215,
    "Contains Duplicate": 217,
    "Invert Binary Tree": 226,
    "Kth Smallest Element in a BST": 230,
    "Lowest Common Ancestor of a BST": 235,
    "Product of Array Except Self": 238,
    "Sliding Window Maximum": 239,
    "Valid Anagram": 242,
    "Binary Tree Right Side View": 199,
    "Number of Islands": 200,
    "Happy Number": 202,
    "Counting Bits": 338,
    "Coin Change": 322,
    "Number of 1 Bits": 191,
    "Missing Number": 268,
    "Longest Increasing Subsequence": 300,
    "Longest Common Subsequence": 1143,
    "Combination Sum": 39,
    "Combination Sum II": 40,
    "Combination Sum IV": 377,
    "Decode Ways": 91,
    "Subsets": 78,
    "Subsets II": 90,
    "Permutations": 46,
    "Maximum Product Subarray": 152,
    "Sum of Two Integers": 371,
    "Reverse Bits": 190,
    "Palindromic Substrings": 647,
    "Pacific Atlantic Water Flow": 417,
    "Graph Valid Tree": 261,
    "Number of Connected Components in an Undirected Graph": 323,
    "Alien Dictionary": 269,
    "Longest Consecutive Sequence": 128,
    "Non-overlapping Intervals": 435,
    "Meeting Rooms": 252,
    "Meeting Rooms II": 253,
    "Encode and Decode Strings": 271,
    "Subtree of Another Tree": 572,
    "Serialize and Deserialize Binary Tree": 297,
    "Validate Binary Search Tree": 98,
    "Balanced Binary Tree": 110,
    "Count Good Nodes in Binary Tree": 1448,
    "Kth Largest Element in a Stream": 703,
    "Last Stone Weight": 1046,
    "K Closest Points to Origin": 973,
    "Task Scheduler": 621,
    "Design Twitter": 355,
    "Top K Frequent Elements": 347,
    "Find Median from Data Stream": 295,
    "Car Fleet": 853,
    "Daily Temperatures": 739,
    "Diameter of Binary Tree": 543,
    "Binary Search": 704,
    "Koko Eating Bananas": 875,
    "Time Based Key-Value Store": 981,
    "Find the Duplicate Number": 287,
    "Copy List with Random Pointer": 138,
    "Add Two Numbers": 2,
    "Palindrome Partitioning": 131,
    "N-Queens": 51,
    "Max Area of Island": 695,
    "Surrounded Regions": 130,
    "Rotting Oranges": 994,
    "Redundant Connection": 684,
    "Word Ladder": 127,
    "Min Cost to Connect All Points": 1584,
    "Network Delay Time": 743,
    "Swim in Rising Water": 778,
    "Cheapest Flights Within K Stops": 787,
    "Interleaving String": 97,
    "Edit Distance": 72,
    "Distinct Subsequences": 115,
    "Target Sum": 494,
    "Burst Balloons": 312,
    "Longest Increasing Path in a Matrix": 329,
    "Coin Change II": 518,
    "Hand of Straights": 846,
    "Merge Triplets to Form Target Triplet": 1899,
    "Partition Labels": 763,
    "Valid Parenthesis String": 678,
    "Maximum Length of Pair Chain": 646,
    "Two Sum II - Input Array Is Sorted": 167,
    "Permutation in String": 567,
    "Minimum Window Substring": 76,
    "Longest Repeating Character Replacement": 424,
    "Plus One": 66,
    "Multiply Strings": 43,
    "Detect Squares": 2013,
    "Partition Equal Subset Sum": 416,
    "Minimum Interval to Include Each Query": 1851,
    "Reconstruct Itinerary": 332,
    "Walls and Gates": 286,
    "Valid Sudoku": 36,
}


def add_leetcode_no_to_yaml(filepath: Path) -> bool:
    """Add leetcode_no field to a YAML file after sequence_number."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Check if leetcode_no already exists
    if "leetcode_no:" in content:
        print(f"  Skipping {filepath.name} - already has leetcode_no")
        return False

    # Extract title
    title_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
    if not title_match:
        print(f"  ERROR: No title found in {filepath.name}")
        return False

    title = title_match.group(1).strip()

    # Look up LeetCode number
    leetcode_no = LEETCODE_MAPPING.get(title)

    if leetcode_no is None:
        print(f"  WARNING: No LeetCode mapping for '{title}' ({filepath.name})")
        # Still add the field but with null value
        leetcode_line = "leetcode_no: null"
    else:
        leetcode_line = f"leetcode_no: {leetcode_no}"

    # Insert after sequence_number line
    new_content = re.sub(
        r"(^sequence_number:\s*\d+\s*$)",
        rf"\1\n{leetcode_line}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    if new_content == content:
        print(f"  ERROR: Could not find sequence_number in {filepath.name}")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  Updated {filepath.name}: {leetcode_line}")
    return True


def main():
    """Update all problem YAML files with leetcode_no."""
    problems_dir = Path(__file__).parent.parent / "data" / "problems"

    if not problems_dir.exists():
        print(f"ERROR: Problems directory not found: {problems_dir}")
        return

    yaml_files = sorted(problems_dir.glob("*.yaml"))

    print(f"Found {len(yaml_files)} YAML files in {problems_dir}")
    print()

    updated = 0
    skipped = 0
    errors = 0

    for yaml_file in yaml_files:
        try:
            if add_leetcode_no_to_yaml(yaml_file):
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR processing {yaml_file.name}: {e}")
            errors += 1

    print()
    print(f"Summary: {updated} updated, {skipped} skipped, {errors} errors")


if __name__ == "__main__":
    main()
