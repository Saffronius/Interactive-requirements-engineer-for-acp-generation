#!/usr/bin/env python3
"""
Basic usage example of the Vector Search Agent.
This example demonstrates how to:
1. Initialize the search agent
2. Create an index
3. Ingest documents
4. Perform various types of searches
"""

import asyncio
import os
from typing import List, Dict, Any

# Add the src directory to the path so we can import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from search_agent import SearchAgent, VectorStoreType


async def main():
    """Main example function."""
    print("🚀 Vector Search Agent - Basic Usage Example")
    print("=" * 50)
    
    # Initialize the search agent with Pinecone MCP
    agent = SearchAgent(
        store_type=VectorStoreType.PINECONE_MCP,
        store_config={}
    )
    
    print("✅ Search agent initialized")
    
    # Health check
    health = await agent.health_check()
    print(f"📊 Health check: {health}")
    
    # Example documents
    sample_documents = [
        {
            "id": "doc_1",
            "text": "Python is a high-level programming language known for its simplicity and readability.",
            "metadata": {"category": "programming", "language": "python", "difficulty": "beginner"}
        },
        {
            "id": "doc_2", 
            "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that improve through experience.",
            "metadata": {"category": "ai", "topic": "machine_learning", "difficulty": "intermediate"}
        },
        {
            "id": "doc_3",
            "text": "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently.",
            "metadata": {"category": "database", "topic": "vector_search", "difficulty": "advanced"}
        },
        {
            "id": "doc_4",
            "text": "FastAPI is a modern, fast web framework for building APIs with Python based on standard Python type hints.",
            "metadata": {"category": "programming", "language": "python", "difficulty": "intermediate"}
        },
        {
            "id": "doc_5",
            "text": "Semantic search uses natural language processing to understand the meaning and context of search queries.",
            "metadata": {"category": "search", "topic": "semantic_search", "difficulty": "advanced"}
        }
    ]
    
    # Create an index
    index_name = "demo-index"
    print(f"\n📝 Creating index: {index_name}")
    success = await agent.create_index(index_name)
    if success:
        print("✅ Index created successfully")
    else:
        print("❌ Failed to create index")
        return
    
    # Ingest documents
    print(f"\n📚 Ingesting {len(sample_documents)} documents...")
    success = await agent.ingest_documents(index_name, sample_documents)
    if success:
        print("✅ Documents ingested successfully")
    else:
        print("❌ Failed to ingest documents")
        return
    
    # Get index stats
    print(f"\n📊 Index statistics:")
    stats = await agent.get_index_stats(index_name)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Perform semantic search
    print(f"\n🔍 Semantic Search Examples:")
    queries = [
        "programming languages",
        "artificial intelligence and machine learning",
        "database technology",
        "web development frameworks"
    ]
    
    for query in queries:
        print(f"\n  Query: '{query}'")
        results = await agent.semantic_search(
            index_name=index_name,
            query=query,
            top_k=3
        )
        
        for i, result in enumerate(results, 1):
            print(f"    {i}. [Score: {result.score:.3f}] {result.text[:80]}...")
            print(f"       Metadata: {result.metadata}")
    
    # Perform search with filtering
    print(f"\n🔍 Filtered Search Example:")
    query = "programming"
    filter_condition = {"category": "programming"}
    print(f"  Query: '{query}' with filter: {filter_condition}")
    
    results = await agent.semantic_search(
        index_name=index_name,
        query=query,
        top_k=5,
        filter=filter_condition
    )
    
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] {result.text[:80]}...")
        print(f"       Metadata: {result.metadata}")
    
    # Perform search with similarity threshold
    print(f"\n🔍 Similarity Threshold Search Example:")
    query = "vector search"
    threshold = 0.7
    print(f"  Query: '{query}' with threshold: {threshold}")
    
    results = await agent.similarity_search_with_threshold(
        index_name=index_name,
        query=query,
        similarity_threshold=threshold,
        top_k=5
    )
    
    print(f"  Found {len(results)} results above threshold:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] {result.text[:80]}...")
        print(f"       Metadata: {result.metadata}")
    
    # Perform hybrid search (if supported)
    print(f"\n🔍 Hybrid Search Example:")
    query = "Python programming"
    print(f"  Query: '{query}' (hybrid search)")
    
    results = await agent.hybrid_search(
        index_name=index_name,
        query=query,
        top_k=3,
        alpha=0.7,  # Weight towards semantic search
        rerank=True,
        rerank_top_n=2
    )
    
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] {result.text[:80]}...")
        print(f"       Metadata: {result.metadata}")
    
    # Demonstrate vector store switching
    print(f"\n🔄 Vector Store Switching Example:")
    print("  Current store:", agent.store_type.value)
    
    # Switch to Qdrant (this would require Qdrant to be running)
    try:
        agent.switch_vector_store(
            VectorStoreType.QDRANT,
            {"host": "localhost", "port": 6333}
        )
        print("  Switched to:", agent.store_type.value)
        
        # Switch back to Pinecone MCP
        agent.switch_vector_store(VectorStoreType.PINECONE_MCP, {})
        print("  Switched back to:", agent.store_type.value)
        
    except Exception as e:
        print(f"  Note: Vector store switching failed (expected if Qdrant not running): {e}")
    
    print(f"\n🎉 Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 