#!/usr/bin/env python3
"""
Simple command-line calculator application.
"""

import argparse
from calculator import calculate

def main():
    parser = argparse.ArgumentParser(
        description="Simple CLI calculator: <number> <op> <number>"
    )
    parser.add_argument('expression', nargs=3,
                        help="Expression: <number> <operator> <number>")
    args = parser.parse_args()
    expr = ' '.join(args.expression)
    try:
        result = calculate(expr)
        print(result)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
