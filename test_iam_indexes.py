#!/usr/bin/env python3
"""
Test script to verify IAM indexes exist and contain data
"""

import sys
import os
import asyncio

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

async def test_indexes():
    try:
        from src.vector_store.pinecone_mcp_real import PineconeMCPRealStore
        from src.vector_store.base import SearchRequest, SearchType
        print("✅ Successfully imported MCP classes")
        
        # Initialize the store
        store = PineconeMCPRealStore()
        print("✅ Initialized MCP store")
        
        # Test indexes
        test_indexes = [
            ("iam-policy-guide-fine", "aws-iam-detailed"),
            ("iam-policy-guide-context", "aws-iam-examples")
        ]
        
        for index_name, namespace in test_indexes:
            print(f"\n🔍 Testing index: {index_name}, namespace: {namespace}")
            try:
                # Create a proper SearchRequest
                request = SearchRequest(
                    query="IAM policy S3 access",
                    top_k=3,
                    namespace=namespace,
                    search_type=SearchType.SEMANTIC
                )
                
                # Try a simple search
                results = await store.search(
                    index_name=index_name,
                    request=request
                )
                print(f"✅ Found {len(results)} results in {index_name}")
                if results:
                    print(f"   Sample result: {results[0].text[:100]}...")
                else:
                    print("   No results found")
            except Exception as e:
                print(f"❌ Error searching {index_name}: {e}")
        
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        print("This might mean the indexes don't exist or there's a configuration issue")

if __name__ == "__main__":
    asyncio.run(test_indexes()) 