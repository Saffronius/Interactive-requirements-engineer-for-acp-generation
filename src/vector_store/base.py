from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class SearchType(str, Enum):
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


class Document(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    search_type: SearchType = SearchType.SEMANTIC
    top_k: int = 10
    filter: Optional[Dict[str, Any]] = None
    namespace: Optional[str] = None
    # Hybrid search parameters
    alpha: Optional[float] = None  # For hybrid search weighting
    rerank: bool = False
    rerank_top_n: Optional[int] = None


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def create_index(self, name: str, dimension: int, **kwargs) -> bool:
        """Create a new index."""
        pass
    
    @abstractmethod
    async def delete_index(self, name: str) -> bool:
        """Delete an index."""
        pass
    
    @abstractmethod
    async def list_indexes(self) -> List[str]:
        """List all available indexes."""
        pass
    
    @abstractmethod
    async def upsert_documents(
        self, 
        index_name: str, 
        documents: List[Document], 
        namespace: Optional[str] = None
    ) -> bool:
        """Insert or update documents in the vector store."""
        pass
    
    @abstractmethod
    async def search(
        self, 
        index_name: str, 
        request: SearchRequest
    ) -> List[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def delete_documents(
        self, 
        index_name: str, 
        ids: List[str], 
        namespace: Optional[str] = None
    ) -> bool:
        """Delete documents by IDs."""
        pass
    
    @abstractmethod
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics about an index."""
        pass 