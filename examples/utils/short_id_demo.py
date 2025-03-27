#!/usr/bin/env python
"""
Short ID Demo

This script demonstrates the generation of short IDs using the ID generator utility.
"""

from roboco.utils.id_generator import generate_short_id

def main():
    """Generate and display various short IDs."""
    print("Generating short IDs (default 8-character length):")
    for i in range(5):
        print(f"ID {i+1}: {generate_short_id()}")
        
    print("\nGenerating short IDs with different lengths:")
    for length in [4, 6, 10, 12]:
        print(f"{length}-character ID: {generate_short_id(length)}")
        
    print("\nDemonstrating URL usage:")
    short_id = generate_short_id(6)
    print(f"Original URL: https://example.com/projects/3f7d8a9b-2c4e-5f6g-7h8i-9j0k1l2m3n4o")
    print(f"With short ID: https://example.com/projects/{short_id}")

if __name__ == "__main__":
    main() 