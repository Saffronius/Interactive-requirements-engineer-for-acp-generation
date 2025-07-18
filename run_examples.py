#!/usr/bin/env python3
"""
Script to run the vector search agent examples.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def print_banner(title: str):
    """Print a formatted banner."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

async def run_basic_example():
    """Run the basic usage example."""
    print_banner("BASIC USAGE EXAMPLE")
    
    try:
        # Import and run the basic example
        from examples.basic_usage import main
        await main()
    except Exception as e:
        print(f"❌ Error running basic example: {e}")
        return False
    
    return True

async def run_advanced_example():
    """Run the advanced usage example."""
    print_banner("ADVANCED USAGE EXAMPLE")
    
    try:
        # Import and run the advanced example
        from examples.advanced_usage import main
        await main()
    except Exception as e:
        print(f"❌ Error running advanced example: {e}")
        return False
    
    return True

async def main():
    """Main function to run examples."""
    print_banner("VECTOR SEARCH AGENT - EXAMPLES")
    print("This script demonstrates the capabilities of the Vector Search Agent")
    print("using both basic and advanced usage patterns.")
    
    # Check if we can import the required modules
    try:
        from search_agent import SearchAgent, VectorStoreType
        print("✅ Vector Search Agent modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import required modules: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return
    
    # Run examples
    examples = [
        ("Basic Usage", run_basic_example),
        ("Advanced Usage", run_advanced_example)
    ]
    
    results = []
    for name, example_func in examples:
        print(f"\n🚀 Running {name} Example...")
        try:
            success = await example_func()
            results.append((name, success))
        except KeyboardInterrupt:
            print(f"\n⏹️  {name} example interrupted by user")
            results.append((name, False))
            break
        except Exception as e:
            print(f"❌ Unexpected error in {name} example: {e}")
            results.append((name, False))
    
    # Print summary
    print_banner("EXAMPLES SUMMARY")
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    total_run = len(results)
    print(f"\nTotal: {total_passed}/{total_run} examples passed")
    
    if total_passed == total_run:
        print("🎉 All examples completed successfully!")
    else:
        print("⚠️  Some examples failed. Check the output above for details.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 