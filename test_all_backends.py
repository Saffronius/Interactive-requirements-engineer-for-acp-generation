#!/usr/bin/env python3
"""
Test script to verify all 3 vector store backends work properly.
"""

import asyncio
import os
from dotenv import load_dotenv
from src.search_agent import SearchAgent, VectorStoreType

# Load environment variables
load_dotenv()

async def test_backend(store_type: VectorStoreType, config: dict):
    """Test a specific backend configuration."""
    print(f"\n{'='*50}")
    print(f"Testing {store_type.value.upper()} Backend")
    print(f"{'='*50}")
    
    try:
        # Initialize agent
        agent = SearchAgent(store_type=store_type, store_config=config)
        print(f"✅ Agent initialized successfully")
        
        # Test health check
        health = await agent.health_check()
        print(f"✅ Health check: {health['status']}")
        
        # Test list indexes
        indexes = await agent.list_indexes()
        print(f"✅ Listed indexes: {indexes}")
        
        # Test create index (small dimension for testing)
        test_index = f"test-{store_type.value.replace('_', '-')}"
        success = await agent.create_index(test_index, dimension=384)
        if success:
            print(f"✅ Created test index: {test_index}")
        else:
            print(f"⚠️  Index creation returned False (may already exist)")
        
        # Test document ingestion
        test_docs = [
            {
                "id": "test-1",
                "text": f"This is a test document for {store_type.value} backend",
                "metadata": {"backend": store_type.value, "test": True}
            }
        ]
        
        success = await agent.ingest_documents(test_index, test_docs)
        if success:
            print(f"✅ Ingested test documents")
        else:
            print(f"❌ Failed to ingest documents")
        
        # Test semantic search
        results = await agent.semantic_search(
            test_index,
            "test document",
            top_k=3
        )
        print(f"✅ Semantic search returned {len(results)} results")
        
        # Test get stats
        stats = await agent.get_index_stats(test_index)
        print(f"✅ Got index stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {store_type.value}: {e}")
        return False

async def main():
    """Test all available backends."""
    print("Vector Search Agent - Backend Testing")
    print("====================================")
    
    # Check environment variables
    pinecone_key = os.getenv("PINECONE_API_KEY")
    print(f"PINECONE_API_KEY configured: {'✅ Yes' if pinecone_key else '❌ No'}")
    
    # Configure backends
    configs = {
        VectorStoreType.PINECONE_MCP: {
            # MCP uses environment variables automatically
        },
        VectorStoreType.PINECONE: {
            "api_key": pinecone_key,
            "environment": os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        },
        VectorStoreType.QDRANT: {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": int(os.getenv("QDRANT_PORT", "6333")),
            "api_key": os.getenv("QDRANT_API_KEY")
        }
    }
    
    results = {}
    
    # Test each backend
    for store_type, config in configs.items():
        # Skip backends that aren't configured
        if store_type == VectorStoreType.PINECONE and not config.get("api_key"):
            print(f"\n⏭️  Skipping {store_type.value} - API key not configured")
            continue
            
        if store_type == VectorStoreType.PINECONE_MCP and not pinecone_key:
            print(f"\n⏭️  Skipping {store_type.value} - API key not configured")
            continue
            
        results[store_type.value] = await test_backend(store_type, config)
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    for backend, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{backend:15} : {status}")
    
    print(f"\nTotal backends tested: {len(results)}")
    print(f"Successful: {sum(results.values())}")
    print(f"Failed: {len(results) - sum(results.values())}")

if __name__ == "__main__":
    asyncio.run(main()) 