from typing import List, Dict, Any, Optional, Union
import asyncio
from enum import Enum

try:
    # Try relative imports first (when run as module)
    from .vector_store.base import VectorStore, Document, SearchResult, SearchRequest, SearchType
    from .vector_store.pinecone_store import PineconeStore
    from .vector_store.pinecone_mcp_store import PineconeMCPStore
    from .vector_store.pinecone_mcp_enhanced import PineconeMCPEnhancedStore
    from .vector_store.qdrant_store import QdrantStore
except ImportError:
    # Fall back to absolute imports (when run as script)
    from vector_store.base import VectorStore, Document, SearchResult, SearchRequest, SearchType
    from vector_store.pinecone_store import PineconeStore
    from vector_store.pinecone_mcp_store import PineconeMCPStore
    from vector_store.pinecone_mcp_enhanced import PineconeMCPEnhancedStore
    from vector_store.qdrant_store import QdrantStore


class VectorStoreType(Enum):
    PINECONE = "pinecone"
    PINECONE_MCP = "pinecone_mcp"
    PINECONE_MCP_ENHANCED = "pinecone_mcp_enhanced"
    QDRANT = "qdrant"


class SearchAgent:
    """Main search agent that coordinates vector store operations."""
    
    def __init__(
        self,
        store_type: VectorStoreType = VectorStoreType.PINECONE_MCP,
        store_config: Optional[Dict[str, Any]] = None
    ):
        self.store_type = store_type
        self.store_config = store_config or {}
        self.vector_store = self._initialize_store()
    
    def _initialize_store(self) -> VectorStore:
        """Initialize the appropriate vector store based on configuration."""
        if self.store_type == VectorStoreType.PINECONE:
            return PineconeStore(**self.store_config)
        elif self.store_type == VectorStoreType.PINECONE_MCP:
            return PineconeMCPStore(**self.store_config)
        elif self.store_type == VectorStoreType.PINECONE_MCP_ENHANCED:
            return PineconeMCPEnhancedStore(**self.store_config)
        elif self.store_type == VectorStoreType.QDRANT:
            return QdrantStore(**self.store_config)
        else:
            raise ValueError(f"Unsupported vector store type: {self.store_type}")
    
    async def create_index(
        self,
        name: str,
        dimension: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Create a new vector index."""
        return await self.vector_store.create_index(name, dimension, **kwargs)
    
    async def delete_index(self, name: str) -> bool:
        """Delete a vector index."""
        return await self.vector_store.delete_index(name)
    
    async def list_indexes(self) -> List[str]:
        """List all available indexes."""
        return await self.vector_store.list_indexes()
    
    async def ingest_documents(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> bool:
        """Ingest documents into the vector store."""
        # Convert dict documents to Document objects
        doc_objects = []
        for i, doc in enumerate(documents):
            doc_obj = Document(
                id=doc.get("id", f"doc_{i}"),
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {}),
                embedding=doc.get("embedding")
            )
            doc_objects.append(doc_obj)
        
        return await self.vector_store.upsert_documents(index_name, doc_objects, namespace)
    
    async def semantic_search(
        self,
        index_name: str,
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """Perform semantic search."""
        request = SearchRequest(
            query=query,
            search_type=SearchType.SEMANTIC,
            top_k=top_k,
            filter=filter,
            namespace=namespace
        )
        return await self.vector_store.search(index_name, request)
    
    async def hybrid_search(
        self,
        index_name: str,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        rerank: bool = False,
        rerank_top_n: Optional[int] = None
    ) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword search."""
        request = SearchRequest(
            query=query,
            search_type=SearchType.HYBRID,
            top_k=top_k,
            filter=filter,
            namespace=namespace,
            alpha=alpha,
            rerank=rerank,
            rerank_top_n=rerank_top_n
        )
        return await self.vector_store.search(index_name, request)
    
    async def search_with_reranking(
        self,
        index_name: str,
        query: str,
        top_k: int = 20,
        rerank_top_n: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """Perform search with reranking for improved relevance."""
        request = SearchRequest(
            query=query,
            search_type=SearchType.SEMANTIC,
            top_k=top_k,
            filter=filter,
            namespace=namespace,
            rerank=True,
            rerank_top_n=rerank_top_n
        )
        return await self.vector_store.search(index_name, request)
    
    async def cascading_search(
        self,
        indexes: List[Dict[str, str]],
        query: str,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        rerank_top_n: Optional[int] = None
    ) -> List[SearchResult]:
        """Perform cascading search across multiple indexes."""
        if isinstance(self.vector_store, PineconeMCPStore):
            request = SearchRequest(
                query=query,
                search_type=SearchType.SEMANTIC,
                top_k=top_k,
                filter=filter,
                rerank=True,
                rerank_top_n=rerank_top_n
            )
            return await self.vector_store.cascading_search(indexes, request)
        else:
            # For other stores, perform search across each index and combine results
            all_results = []
            for index_config in indexes:
                request = SearchRequest(
                    query=query,
                    search_type=SearchType.SEMANTIC,
                    top_k=top_k,
                    filter=filter,
                    namespace=index_config.get("namespace")
                )
                results = await self.vector_store.search(index_config["name"], request)
                all_results.extend(results)
            
            # Sort by score and return top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            return all_results[:top_k]
    
    async def delete_documents(
        self,
        index_name: str,
        document_ids: List[str],
        namespace: Optional[str] = None
    ) -> bool:
        """Delete documents from the vector store."""
        return await self.vector_store.delete_documents(index_name, document_ids, namespace)
    
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics about an index."""
        return await self.vector_store.get_index_stats(index_name)
    
    async def batch_ingest(
        self,
        index_name: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100,
        namespace: Optional[str] = None
    ) -> bool:
        """Ingest documents in batches for better performance."""
        total_docs = len(documents)
        success_count = 0
        
        for i in range(0, total_docs, batch_size):
            batch = documents[i:i + batch_size]
            success = await self.ingest_documents(index_name, batch, namespace)
            if success:
                success_count += len(batch)
            
            # Add a small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        return success_count == total_docs
    
    async def similarity_search_with_threshold(
        self,
        index_name: str,
        query: str,
        similarity_threshold: float = 0.7,
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None
    ) -> List[SearchResult]:
        """Perform similarity search with a minimum threshold."""
        results = await self.semantic_search(
            index_name=index_name,
            query=query,
            top_k=top_k,
            filter=filter,
            namespace=namespace
        )
        
        # Filter results by similarity threshold
        return [result for result in results if result.score >= similarity_threshold]
    
    def switch_vector_store(
        self,
        new_store_type: VectorStoreType,
        new_store_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Switch to a different vector store implementation."""
        self.store_type = new_store_type
        self.store_config = new_store_config or {}
        self.vector_store = self._initialize_store()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store connection."""
        try:
            indexes = await self.list_indexes()
            return {
                "status": "healthy",
                "store_type": self.store_type.value,
                "available_indexes": len(indexes),
                "indexes": indexes
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "store_type": self.store_type.value,
                "error": str(e)
            } 