import os
from typing import List, Dict, Any, Optional
import asyncio
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import numpy as np

try:
    from .base import VectorStore, Document, SearchResult, SearchRequest, SearchType
except ImportError:
    from base import VectorStore, Document, SearchResult, SearchRequest, SearchType


class PineconeStore(VectorStore):
    """Pinecone implementation of the vector store interface."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        environment: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.api_key = api_key or os.getenv("PINECONE_API_KEY")
        self.environment = environment or os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required")
        
        self.pc = Pinecone(api_key=self.api_key)
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
        """Create a new Pinecone index."""
        try:
            if dimension is None:
                dimension = self._embedding_dimension
            
            # Check if index already exists
            existing_indexes = self.pc.list_indexes()
            if name in [idx.name for idx in existing_indexes]:
                print(f"Index '{name}' already exists")
                return True
            
            # Create serverless index
            self.pc.create_index(
                name=name,
                dimension=dimension,
                metric=kwargs.get("metric", "cosine"),
                spec=ServerlessSpec(
                    cloud=kwargs.get("cloud", "aws"),
                    region=kwargs.get("region", self.environment)
                )
            )
            
            # Wait for index to be ready
            while not self.pc.describe_index(name).status['ready']:
                await asyncio.sleep(1)
            
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    async def delete_index(self, name: str) -> bool:
        """Delete a Pinecone index."""
        try:
            self.pc.delete_index(name)
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False
    
    async def list_indexes(self) -> List[str]:
        """List all available Pinecone indexes."""
        try:
            indexes = self.pc.list_indexes()
            return [idx.name for idx in indexes]
        except Exception as e:
            print(f"Error listing indexes: {e}")
            return []
    
    async def upsert_documents(
        self, 
        index_name: str, 
        documents: List[Document], 
        namespace: Optional[str] = None
    ) -> bool:
        """Insert or update documents in Pinecone."""
        try:
            index = self.pc.Index(index_name)
            
            # Prepare vectors for upsert
            vectors = []
            for doc in documents:
                # Generate embedding if not provided
                if doc.embedding is None:
                    embedding = self._encode_text(doc.text)
                else:
                    embedding = doc.embedding
                
                vector = {
                    "id": doc.id,
                    "values": embedding,
                    "metadata": {
                        "text": doc.text,
                        **doc.metadata
                    }
                }
                vectors.append(vector)
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch, namespace=namespace)
            
            return True
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return False
    
    async def search(
        self, 
        index_name: str, 
        request: SearchRequest
    ) -> List[SearchResult]:
        """Search for similar documents in Pinecone."""
        try:
            index = self.pc.Index(index_name)
            
            # Generate query embedding
            query_embedding = self._encode_text(request.query)
            
            # Prepare search parameters
            search_params = {
                "vector": query_embedding,
                "top_k": request.top_k,
                "include_metadata": True,
                "namespace": request.namespace
            }
            
            # Add filter if provided
            if request.filter:
                search_params["filter"] = request.filter
            
            # Execute search
            if request.search_type == SearchType.HYBRID and request.alpha is not None:
                # For hybrid search, we would need to implement sparse vector support
                # This is a simplified version - in practice, you'd need sparse embeddings
                results = index.query(**search_params)
            else:
                # Pure semantic search
                results = index.query(**search_params)
            
            # Convert results to SearchResult objects
            search_results = []
            for match in results.matches:
                result = SearchResult(
                    id=match.id,
                    score=match.score,
                    text=match.metadata.get("text", ""),
                    metadata={k: v for k, v in match.metadata.items() if k != "text"}
                )
                search_results.append(result)
            
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
        """Delete documents by IDs from Pinecone."""
        try:
            index = self.pc.Index(index_name)
            index.delete(ids=ids, namespace=namespace)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics about a Pinecone index."""
        try:
            index = self.pc.Index(index_name)
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {} 