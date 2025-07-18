#!/usr/bin/env python3
"""
Advanced usage example of the Vector Search Agent.
This example demonstrates:
1. Batch document ingestion
2. Cascading search across multiple indexes
3. Advanced filtering and reranking
4. Namespace management
"""

import asyncio
import os
import json
from typing import List, Dict, Any

# Add the src directory to the path so we can import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from search_agent import SearchAgent, VectorStoreType


def generate_sample_documents(category: str, count: int = 20) -> List[Dict[str, Any]]:
    """Generate sample documents for different categories."""
    documents = []
    
    if category == "technology":
        topics = [
            "artificial intelligence", "machine learning", "deep learning",
            "natural language processing", "computer vision", "robotics",
            "blockchain", "cryptocurrency", "quantum computing", "cloud computing",
            "cybersecurity", "data science", "big data", "IoT", "5G",
            "augmented reality", "virtual reality", "edge computing", "DevOps", "microservices"
        ]
        
        for i in range(count):
            topic = topics[i % len(topics)]
            documents.append({
                "id": f"tech_{i:03d}",
                "text": f"This document discusses {topic} and its applications in modern technology. "
                       f"It covers the fundamental concepts, implementation strategies, and future prospects "
                       f"of {topic} in various industries and research domains.",
                "metadata": {
                    "category": "technology",
                    "topic": topic.replace(" ", "_"),
                    "difficulty": ["beginner", "intermediate", "advanced"][i % 3],
                    "year": 2020 + (i % 4)
                }
            })
    
    elif category == "science":
        topics = [
            "physics", "chemistry", "biology", "astronomy", "geology",
            "mathematics", "statistics", "neuroscience", "genetics", "ecology",
            "climate science", "materials science", "biochemistry", "biophysics", "pharmacology",
            "marine biology", "evolutionary biology", "molecular biology", "microbiology", "botany"
        ]
        
        for i in range(count):
            topic = topics[i % len(topics)]
            documents.append({
                "id": f"sci_{i:03d}",
                "text": f"This scientific paper explores {topic} research methodologies and findings. "
                       f"The study presents experimental data, theoretical frameworks, and empirical evidence "
                       f"related to {topic} and its interdisciplinary applications.",
                "metadata": {
                    "category": "science",
                    "topic": topic.replace(" ", "_"),
                    "research_level": ["undergraduate", "graduate", "postdoc"][i % 3],
                    "year": 2018 + (i % 6)
                }
            })
    
    elif category == "business":
        topics = [
            "marketing", "finance", "operations", "strategy", "leadership",
            "entrepreneurship", "innovation", "digital transformation", "supply chain", "logistics",
            "human resources", "project management", "risk management", "compliance", "sustainability",
            "customer experience", "brand management", "sales", "consulting", "analytics"
        ]
        
        for i in range(count):
            topic = topics[i % len(topics)]
            documents.append({
                "id": f"biz_{i:03d}",
                "text": f"This business case study examines {topic} strategies and best practices. "
                       f"The analysis includes market research, competitive analysis, and implementation "
                       f"recommendations for {topic} in various organizational contexts.",
                "metadata": {
                    "category": "business",
                    "topic": topic.replace(" ", "_"),
                    "industry": ["tech", "finance", "healthcare", "retail", "manufacturing"][i % 5],
                    "year": 2019 + (i % 5)
                }
            })
    
    return documents


async def main():
    """Main advanced example function."""
    print("🚀 Vector Search Agent - Advanced Usage Example")
    print("=" * 60)
    
    # Initialize the search agent
    agent = SearchAgent(
        store_type=VectorStoreType.PINECONE_MCP,
        store_config={}
    )
    
    print("✅ Search agent initialized")
    
    # Create multiple indexes for different domains
    indexes = ["technology-index", "science-index", "business-index"]
    
    print(f"\n📝 Creating {len(indexes)} indexes...")
    for index_name in indexes:
        success = await agent.create_index(index_name)
        if success:
            print(f"  ✅ {index_name} created")
        else:
            print(f"  ❌ Failed to create {index_name}")
    
    # Generate and ingest documents for each index
    print(f"\n📚 Generating and ingesting documents...")
    
    # Technology documents
    tech_docs = generate_sample_documents("technology", 15)
    print(f"  📊 Ingesting {len(tech_docs)} technology documents...")
    success = await agent.batch_ingest(
        index_name="technology-index",
        documents=tech_docs,
        batch_size=5,
        namespace="tech_docs"
    )
    print(f"  {'✅' if success else '❌'} Technology documents ingested")
    
    # Science documents
    sci_docs = generate_sample_documents("science", 15)
    print(f"  📊 Ingesting {len(sci_docs)} science documents...")
    success = await agent.batch_ingest(
        index_name="science-index",
        documents=sci_docs,
        batch_size=5,
        namespace="sci_docs"
    )
    print(f"  {'✅' if success else '❌'} Science documents ingested")
    
    # Business documents
    biz_docs = generate_sample_documents("business", 15)
    print(f"  📊 Ingesting {len(biz_docs)} business documents...")
    success = await agent.batch_ingest(
        index_name="business-index",
        documents=biz_docs,
        batch_size=5,
        namespace="biz_docs"
    )
    print(f"  {'✅' if success else '❌'} Business documents ingested")
    
    # Display index statistics
    print(f"\n📊 Index Statistics:")
    for index_name in indexes:
        stats = await agent.get_index_stats(index_name)
        print(f"  {index_name}:")
        for key, value in stats.items():
            print(f"    {key}: {value}")
    
    # Perform cascading search across all indexes
    print(f"\n🔍 Cascading Search Example:")
    cascade_indexes = [
        {"name": "technology-index", "namespace": "tech_docs"},
        {"name": "science-index", "namespace": "sci_docs"},
        {"name": "business-index", "namespace": "biz_docs"}
    ]
    
    query = "artificial intelligence applications"
    print(f"  Query: '{query}' across all indexes")
    
    results = await agent.cascading_search(
        indexes=cascade_indexes,
        query=query,
        top_k=6,
        rerank_top_n=3
    )
    
    print(f"  Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] {result.text[:80]}...")
        print(f"       Source: {result.metadata.get('source_index', 'unknown')}")
        print(f"       Category: {result.metadata.get('category', 'unknown')}")
    
    # Advanced filtering examples
    print(f"\n🔍 Advanced Filtering Examples:")
    
    # Filter by year and difficulty
    print(f"  1. Technology documents from 2022+ with advanced difficulty:")
    results = await agent.semantic_search(
        index_name="technology-index",
        query="machine learning deep learning",
        top_k=5,
        filter={"year": {"$gte": 2022}, "difficulty": "advanced"},
        namespace="tech_docs"
    )
    
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] Topic: {result.metadata.get('topic', 'unknown')}")
        print(f"       Year: {result.metadata.get('year')}, Difficulty: {result.metadata.get('difficulty')}")
    
    # Filter by multiple categories
    print(f"  2. Science documents in biology-related fields:")
    results = await agent.semantic_search(
        index_name="science-index",
        query="biological research methods",
        top_k=5,
        filter={"topic": {"$in": ["biology", "genetics", "molecular_biology", "marine_biology"]}},
        namespace="sci_docs"
    )
    
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] Topic: {result.metadata.get('topic', 'unknown')}")
        print(f"       Research Level: {result.metadata.get('research_level')}")
    
    # Search with reranking
    print(f"\n🔍 Search with Reranking Example:")
    query = "innovation and digital transformation"
    print(f"  Query: '{query}' with reranking")
    
    results = await agent.search_with_reranking(
        index_name="business-index",
        query=query,
        top_k=10,
        rerank_top_n=3,
        namespace="biz_docs"
    )
    
    print(f"  Top {len(results)} reranked results:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] Topic: {result.metadata.get('topic', 'unknown')}")
        print(f"       Industry: {result.metadata.get('industry')}")
    
    # Demonstrate namespace-based operations
    print(f"\n🏷️  Namespace Management Example:")
    
    # Search within specific namespace
    print(f"  Searching within 'tech_docs' namespace:")
    results = await agent.semantic_search(
        index_name="technology-index",
        query="quantum computing",
        top_k=3,
        namespace="tech_docs"
    )
    
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] {result.text[:60]}...")
    
    # Similarity threshold search
    print(f"\n🎯 Similarity Threshold Search:")
    query = "data science and analytics"
    threshold = 0.8
    print(f"  Query: '{query}' with threshold: {threshold}")
    
    results = await agent.similarity_search_with_threshold(
        index_name="technology-index",
        query=query,
        similarity_threshold=threshold,
        top_k=10,
        namespace="tech_docs"
    )
    
    print(f"  Found {len(results)} high-similarity results:")
    for i, result in enumerate(results, 1):
        print(f"    {i}. [Score: {result.score:.3f}] Topic: {result.metadata.get('topic', 'unknown')}")
    
    # Cleanup example (optional)
    print(f"\n🧹 Cleanup Example:")
    print("  Note: Uncomment the following lines to delete test documents")
    
    # Delete some documents by ID
    # tech_doc_ids = [f"tech_{i:03d}" for i in range(5)]
    # success = await agent.delete_documents("technology-index", tech_doc_ids, "tech_docs")
    # print(f"  {'✅' if success else '❌'} Deleted {len(tech_doc_ids)} technology documents")
    
    print(f"\n🎉 Advanced example completed successfully!")
    print("\nKey features demonstrated:")
    print("  ✅ Batch document ingestion")
    print("  ✅ Multiple index management")
    print("  ✅ Cascading search across indexes")
    print("  ✅ Advanced filtering with MongoDB-style queries")
    print("  ✅ Namespace-based document organization")
    print("  ✅ Search with reranking")
    print("  ✅ Similarity threshold filtering")


if __name__ == "__main__":
    asyncio.run(main()) 