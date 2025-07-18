from typing import List, Dict, Any, Optional
import asyncio
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

try:
    from .base import VectorStore, Document, SearchResult, SearchRequest, SearchType
except ImportError:
    from base import VectorStore, Document, SearchResult, SearchRequest, SearchType


class QdrantStore(VectorStore):
    """Qdrant implementation of the vector store interface."""
    
    def __init__(
        self, 
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.client = QdrantClient(host=host, port=port, api_key=api_key)
        self.embedding_model = SentenceTransformer(embedding_model)
        self._embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
    
    def _encode_text(self, text: str) -> List[float]:
        """Encode text to embedding vector."""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def _encode_texts(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts to embedding vectors."""
        embeddings = self.embedding_model.encode(texts)
        return embeddings.tolist()
    
    async def create_index(self, name: str, dimension: int = None, **kwargs) -> bool:
        """Create a new Qdrant collection."""
        try:
            if dimension is None:
                dimension = self._embedding_dimension
            
            # Check if collection already exists
            collections = self.client.get_collections()
            if name in [col.name for col in collections.collections]:
                print(f"Collection '{name}' already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    async def delete_index(self, name: str) -> bool:
        """Delete a Qdrant collection."""
        try:
            self.client.delete_collection(collection_name=name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False
    
    async def list_indexes(self) -> List[str]:
        """List all available Qdrant collections."""
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    async def upsert_documents(
        self, 
        index_name: str, 
        documents: List[Document], 
        namespace: Optional[str] = None
    ) -> bool:
        """Insert or update documents in Qdrant."""
        try:
            points = []
            for doc in documents:
                # Generate embedding if not provided
                if doc.embedding is None:
                    embedding = self._encode_text(doc.text)
                else:
                    embedding = doc.embedding
                
                # Prepare payload
                payload = {
                    "text": doc.text,
                    **doc.metadata
                }
                
                # Add namespace to payload if provided
                if namespace:
                    payload["namespace"] = namespace
                
                point = PointStruct(
                    id=doc.id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upsert points
            self.client.upsert(
                collection_name=index_name,
                points=points
            )
            return True
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return False
    
    async def search(
        self, 
        index_name: str, 
        request: SearchRequest
    ) -> List[SearchResult]:
        """Search for similar documents in Qdrant."""
        try:
            # Generate query embedding
            query_embedding = self._encode_text(request.query)
            
            # Prepare search filter
            search_filter = None
            if request.filter or request.namespace:
                conditions = []
                
                # Add namespace filter
                if request.namespace:
                    conditions.append(
                        FieldCondition(
                            key="namespace",
                            match=MatchValue(value=request.namespace)
                        )
                    )
                
                # Add custom filters
                if request.filter:
                    for key, value in request.filter.items():
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Execute search
            results = self.client.search(
                collection_name=index_name,
                query_vector=query_embedding,
                limit=request.top_k,
                query_filter=search_filter
            )
            
            # Convert results to SearchResult objects
            search_results = []
            for result in results:
                search_result = SearchResult(
                    id=str(result.id),
                    score=result.score,
                    text=result.payload.get("text", ""),
                    metadata={k: v for k, v in result.payload.items() if k not in ["text", "namespace"]}
                )
                search_results.append(search_result)
            
            return search_results
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    async def delete_documents(
        self, 
        index_name: str, 
        ids: List[str], 
        namespace: Optional[str] = None
    ) -> bool:
        """Delete documents by IDs from Qdrant."""
        try:
            if namespace:
                # Delete with namespace filter
                self.client.delete(
                    collection_name=index_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="namespace",
                                match=MatchValue(value=namespace)
                            )
                        ]
                    )
                )
            else:
                # Delete by IDs
                self.client.delete(
                    collection_name=index_name,
                    points_selector=ids
                )
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics about a Qdrant collection."""
        try:
            info = self.client.get_collection(collection_name=index_name)
            return {
                "total_vector_count": info.points_count,
                "dimension": info.config.params.vectors.size,
                "index_fullness": 0.0,  # Qdrant doesn't have this concept
                "namespaces": {}  # Would need to aggregate from payloads
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {} 