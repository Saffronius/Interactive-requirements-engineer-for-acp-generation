#!/usr/bin/env python3
"""
Test script to demonstrate MCP integration with Pinecone.
This script tests the actual MCP functions and shows how they work.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_mcp_functions():
    """Test the actual MCP functions directly."""
    print("🧪 Testing Pinecone MCP Functions")
    print("=" * 50)
    
    # Test 1: List indexes
    print("\n1. Testing list_indexes...")
    try:
        # This should work with your MCP setup
        from mcp_pinecone import list_indexes
        result = await list_indexes(random_string="test")
        print(f"✅ list_indexes result: {result}")
    except Exception as e:
        print(f"❌ list_indexes failed: {e}")
    
    # Test 2: Create index
    print("\n2. Testing create_index_for_model...")
    try:
        from mcp_pinecone import create_index_for_model
        result = await create_index_for_model(
            name="test-mcp-index",
            embed={
                "model": "multilingual-e5-large",
                "fieldMap": {"text": "text"}
            }
        )
        print(f"✅ create_index_for_model result: {result}")
    except Exception as e:
        print(f"❌ create_index_for_model failed: {e}")
    
    # Test 3: Upsert records
    print("\n3. Testing upsert_records...")
    try:
        from mcp_pinecone import upsert_records
        
        sample_records = [
            {
                "id": "test_doc_1",
                "text": "This is a test document about machine learning and AI.",
                "category": "technology",
                "topic": "ai"
            },
            {
                "id": "test_doc_2", 
                "text": "Python is a versatile programming language used in data science.",
                "category": "programming",
                "topic": "python"
            }
        ]
        
        result = await upsert_records(
            name="test-mcp-index",
            namespace="test-namespace",
            records=sample_records
        )
        print(f"✅ upsert_records result: {result}")
    except Exception as e:
        print(f"❌ upsert_records failed: {e}")
    
    # Test 4: Search records
    print("\n4. Testing search_records...")
    try:
        from mcp_pinecone import search_records
        
        result = await search_records(
            name="test-mcp-index",
            namespace="test-namespace",
            query={
                "topK": 5,
                "inputs": {"text": "machine learning programming"}
            }
        )
        print(f"✅ search_records result: {result}")
    except Exception as e:
        print(f"❌ search_records failed: {e}")
    
    # Test 5: Search with reranking
    print("\n5. Testing search_records with reranking...")
    try:
        from mcp_pinecone import search_records
        
        result = await search_records(
            name="test-mcp-index",
            namespace="test-namespace",
            query={
                "topK": 10,
                "inputs": {"text": "programming languages"}
            },
            rerank={
                "model": "pinecone-rerank-v0",
                "rankFields": ["text"],
                "topN": 3
            }
        )
        print(f"✅ search_records with reranking result: {result}")
    except Exception as e:
        print(f"❌ search_records with reranking failed: {e}")
    
    # Test 6: Describe index stats
    print("\n6. Testing describe_index_stats...")
    try:
        from mcp_pinecone import describe_index_stats
        
        result = await describe_index_stats(name="test-mcp-index")
        print(f"✅ describe_index_stats result: {result}")
    except Exception as e:
        print(f"❌ describe_index_stats failed: {e}")
    
    # Test 7: Rerank documents
    print("\n7. Testing rerank_documents...")
    try:
        from mcp_pinecone import rerank_documents
        
        documents = [
            "Machine learning is a subset of artificial intelligence.",
            "Python is a programming language.",
            "Deep learning uses neural networks.",
            "Data science involves analyzing data."
        ]
        
        result = await rerank_documents(
            model="pinecone-rerank-v0",
            query="artificial intelligence and machine learning",
            documents=documents,
            options={"topN": 3}
        )
        print(f"✅ rerank_documents result: {result}")
    except Exception as e:
        print(f"❌ rerank_documents failed: {e}")


async def test_search_agent_with_mcp():
    """Test the search agent with MCP integration."""
    print("\n\n🤖 Testing Search Agent with MCP Integration")
    print("=" * 50)
    
    try:
        from vector_store.pinecone_mcp_real import PineconeMCPRealStore
        from vector_store.base import Document, SearchRequest, SearchType
        
        # Initialize the real MCP store
        store = PineconeMCPRealStore()
        print("✅ PineconeMCPRealStore initialized")
        
        # Test list indexes
        print("\n1. Testing list_indexes via store...")
        indexes = await store.list_indexes()
        print(f"Available indexes: {indexes}")
        
        # Test create index
        print("\n2. Testing create_index via store...")
        success = await store.create_index("agent-test-index")
        print(f"Index creation success: {success}")
        
        # Test upsert documents
        print("\n3. Testing upsert_documents via store...")
        documents = [
            Document(
                id="agent_doc_1",
                text="Vector databases are optimized for similarity search using embeddings.",
                metadata={"category": "database", "topic": "vector_search"}
            ),
            Document(
                id="agent_doc_2",
                text="Semantic search understands the meaning behind queries, not just keywords.",
                metadata={"category": "search", "topic": "semantic_search"}
            )
        ]
        
        success = await store.upsert_documents("agent-test-index", documents, "agent-test")
        print(f"Document upsert success: {success}")
        
        # Test search
        print("\n4. Testing search via store...")
        request = SearchRequest(
            query="vector similarity search",
            search_type=SearchType.SEMANTIC,
            top_k=5,
            namespace="agent-test"
        )
        
        results = await store.search("agent-test-index", request)
        print(f"Search results: {len(results)} documents found")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [Score: {result.score:.3f}] {result.text}")
        
        # Test search with reranking
        print("\n5. Testing search with reranking via store...")
        request.rerank = True
        request.rerank_top_n = 2
        
        results = await store.search("agent-test-index", request)
        print(f"Reranked search results: {len(results)} documents found")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [Score: {result.score:.3f}] {result.text}")
        
        # Test index stats
        print("\n6. Testing get_index_stats via store...")
        stats = await store.get_index_stats("agent-test-index")
        print(f"Index stats: {stats}")
        
    except Exception as e:
        print(f"❌ Search agent test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Pinecone MCP Integration Test Suite")
    print("=" * 60)
    print("This script tests the integration between the Vector Search Agent")
    print("and Pinecone's MCP (Model Context Protocol) functions.")
    
    # Test MCP functions directly
    await test_mcp_functions()
    
    # Test search agent with MCP
    await test_search_agent_with_mcp()
    
    print("\n\n🎉 MCP Integration Test Complete!")
    print("=" * 60)
    print("If you see errors above, it might be because:")
    print("1. Pinecone API key is not configured")
    print("2. MCP functions are not available in your environment")
    print("3. Network connectivity issues")
    print("\nThe system will fall back to mock implementations when MCP is unavailable.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 