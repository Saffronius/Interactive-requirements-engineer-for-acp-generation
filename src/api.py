from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .search_agent import SearchAgent, VectorStoreType
from .vector_store.base import SearchResult


# Load environment variables
load_dotenv()

# Pydantic models for request/response
class DocumentInput(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    filter: Optional[Dict[str, Any]] = None
    namespace: Optional[str] = None


class HybridSearchRequest(SearchRequest):
    alpha: float = 0.5
    rerank: bool = False
    rerank_top_n: Optional[int] = None


class SearchWithRerankingRequest(SearchRequest):
    rerank_top_n: int = 5


class CascadingSearchRequest(BaseModel):
    indexes: List[Dict[str, str]]
    query: str
    top_k: int = 10
    filter: Optional[Dict[str, Any]] = None
    rerank_top_n: Optional[int] = None


class IndexCreateRequest(BaseModel):
    name: str
    dimension: Optional[int] = None
    metric: str = "cosine"
    cloud: str = "aws"
    region: str = "us-east-1"


class BatchIngestRequest(BaseModel):
    index_name: str
    documents: List[DocumentInput]
    batch_size: int = 100
    namespace: Optional[str] = None


class SimilaritySearchRequest(SearchRequest):
    similarity_threshold: float = 0.7


# Global search agent instance
search_agent: Optional[SearchAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global search_agent
    
    # Get API key from environment
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    
    # Configure for different store types
    store_configs = {
        VectorStoreType.PINECONE: {
            "api_key": pinecone_api_key,
            "environment": os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        },
        VectorStoreType.PINECONE_MCP: {
            # MCP uses environment variables automatically
        },
        VectorStoreType.PINECONE_MCP_ENHANCED: {
            "api_key": pinecone_api_key,
            "embedding_model": "multilingual-e5-large",
            "default_namespace": "default"
        },
        VectorStoreType.QDRANT: {
            "host": os.getenv("QDRANT_HOST", "localhost"),
            "port": int(os.getenv("QDRANT_PORT", "6333")),
            "api_key": os.getenv("QDRANT_API_KEY")
        }
    }
    
    # Default to PINECONE_MCP, but provide config for all
    default_store_type = VectorStoreType.PINECONE_MCP
    search_agent = SearchAgent(
        store_type=default_store_type,
        store_config=store_configs.get(default_store_type, {})
    )
    
    # Store configs for easy switching
    search_agent._store_configs = store_configs
    
    yield
    # Shutdown
    search_agent = None


app = FastAPI(
    title="Vector Search Agent API",
    description="A Python-based search agent using Pinecone as vector store with support for semantic and hybrid search",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    return await search_agent.health_check()


@app.get("/indexes")
async def list_indexes():
    """List all available indexes."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        indexes = await search_agent.list_indexes()
        return {"indexes": indexes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes")
async def create_index(request: IndexCreateRequest):
    """Create a new vector index."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        success = await search_agent.create_index(
            name=request.name,
            dimension=request.dimension,
            metric=request.metric,
            cloud=request.cloud,
            region=request.region
        )
        if success:
            return {"message": f"Index '{request.name}' created successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to create index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/indexes/{index_name}")
async def delete_index(index_name: str):
    """Delete a vector index."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        success = await search_agent.delete_index(index_name)
        if success:
            return {"message": f"Index '{index_name}' deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/indexes/{index_name}/stats")
async def get_index_stats(index_name: str):
    """Get statistics about an index."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        stats = await search_agent.get_index_stats(index_name)
        return {"index_name": index_name, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/documents")
async def ingest_documents(index_name: str, documents: List[DocumentInput], namespace: Optional[str] = None):
    """Ingest documents into the vector store."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        # Convert Pydantic models to dicts
        doc_dicts = [doc.model_dump() for doc in documents]
        success = await search_agent.ingest_documents(index_name, doc_dicts, namespace)
        if success:
            return {"message": f"Successfully ingested {len(documents)} documents"}
        else:
            raise HTTPException(status_code=400, detail="Failed to ingest documents")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/documents/batch")
async def batch_ingest_documents(index_name: str, request: BatchIngestRequest, background_tasks: BackgroundTasks):
    """Ingest documents in batches (background task)."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        # Convert Pydantic models to dicts
        doc_dicts = [doc.model_dump() for doc in request.documents]
        
        # Add background task for batch ingestion
        background_tasks.add_task(
            search_agent.batch_ingest,
            index_name,
            doc_dicts,
            request.batch_size,
            request.namespace
        )
        
        return {"message": f"Batch ingestion of {len(request.documents)} documents started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/search/semantic")
async def semantic_search(index_name: str, request: SearchRequest):
    """Perform semantic search."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        results = await search_agent.semantic_search(
            index_name=index_name,
            query=request.query,
            top_k=request.top_k,
            filter=request.filter,
            namespace=request.namespace
        )
        return {"results": [result.model_dump() for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/search/hybrid")
async def hybrid_search(index_name: str, request: HybridSearchRequest):
    """Perform hybrid search combining semantic and keyword search."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        results = await search_agent.hybrid_search(
            index_name=index_name,
            query=request.query,
            top_k=request.top_k,
            alpha=request.alpha,
            filter=request.filter,
            namespace=request.namespace,
            rerank=request.rerank,
            rerank_top_n=request.rerank_top_n
        )
        return {"results": [result.model_dump() for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/search/rerank")
async def search_with_reranking(index_name: str, request: SearchWithRerankingRequest):
    """Perform search with reranking for improved relevance."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        results = await search_agent.search_with_reranking(
            index_name=index_name,
            query=request.query,
            top_k=request.top_k,
            rerank_top_n=request.rerank_top_n,
            filter=request.filter,
            namespace=request.namespace
        )
        return {"results": [result.model_dump() for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/cascading")
async def cascading_search(request: CascadingSearchRequest):
    """Perform cascading search across multiple indexes."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        results = await search_agent.cascading_search(
            indexes=request.indexes,
            query=request.query,
            top_k=request.top_k,
            filter=request.filter,
            rerank_top_n=request.rerank_top_n
        )
        return {"results": [result.model_dump() for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/indexes/{index_name}/search/similarity")
async def similarity_search_with_threshold(index_name: str, request: SimilaritySearchRequest):
    """Perform similarity search with a minimum threshold."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        results = await search_agent.similarity_search_with_threshold(
            index_name=index_name,
            query=request.query,
            similarity_threshold=request.similarity_threshold,
            top_k=request.top_k,
            filter=request.filter,
            namespace=request.namespace
        )
        return {"results": [result.model_dump() for result in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/indexes/{index_name}/documents")
async def delete_documents(index_name: str, document_ids: List[str], namespace: Optional[str] = None):
    """Delete documents from the vector store."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        success = await search_agent.delete_documents(index_name, document_ids, namespace)
        if success:
            return {"message": f"Successfully deleted {len(document_ids)} documents"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete documents")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/switch-store")
async def switch_vector_store(store_type: VectorStoreType, store_config: Optional[Dict[str, Any]] = None):
    """Switch to a different vector store implementation."""
    if not search_agent:
        raise HTTPException(status_code=503, detail="Search agent not initialized")
    
    try:
        # Use provided config or fall back to stored configs
        if store_config is None and hasattr(search_agent, '_store_configs'):
            store_config = search_agent._store_configs.get(store_type, {})
        
        search_agent.switch_vector_store(store_type, store_config)
        return {
            "message": f"Switched to {store_type.value} vector store",
            "store_type": store_type.value,
            "config_used": bool(store_config)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/available-stores")
async def get_available_stores():
    """Get information about available vector store backends."""
    stores = {
        "pinecone": {
            "name": "Pinecone (Direct API)",
            "description": "Direct integration with Pinecone using pinecone-client",
            "requires": ["PINECONE_API_KEY"],
            "optional": ["PINECONE_ENVIRONMENT"]
        },
        "pinecone_mcp": {
            "name": "Pinecone (MCP)",
            "description": "Pinecone integration via Model Context Protocol",
            "requires": ["PINECONE_API_KEY"],
            "features": ["integrated_inference", "advanced_reranking", "cascading_search"]
        },
        "pinecone_mcp_enhanced": {
            "name": "Pinecone (MCP Enhanced)",
            "description": "Pinecone integration via Model Context Protocol with enhanced features",
            "requires": ["PINECONE_API_KEY"],
            "features": ["integrated_inference", "advanced_reranking", "cascading_search"]
        },
        "qdrant": {
            "name": "Qdrant",
            "description": "Open-source vector database alternative",
            "requires": ["QDRANT_HOST"],
            "optional": ["QDRANT_PORT"]
        }
    }
    
    # Check which stores are properly configured
    configured_stores = {}
    for store_key, store_info in stores.items():
        store_type = VectorStoreType(store_key)
        config_available = False
        
        if hasattr(search_agent, '_store_configs'):
            config = search_agent._store_configs.get(store_type, {})
            # Check if required environment variables are set
            if store_key == "pinecone":
                config_available = bool(config.get("api_key"))
            elif store_key == "pinecone_mcp":
                config_available = bool(os.getenv("PINECONE_API_KEY"))
            elif store_key == "pinecone_mcp_enhanced":
                config_available = bool(config.get("api_key"))
            elif store_key == "qdrant":
                config_available = bool(config.get("host"))
        
        configured_stores[store_key] = {
            **store_info,
            "configured": config_available,
            "current": search_agent.store_type.value == store_key if search_agent else False
        }
    
    return {"stores": configured_stores}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 