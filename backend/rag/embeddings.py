"""
Embedding generation service for RAG system.
Supports multiple embedding models for medical knowledge vectorization.
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import CohereEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import settings


class EmbeddingModel(str, Enum):
    """Available embedding models."""
    OPENAI_LARGE = "text-embedding-3-large"
    OPENAI_SMALL = "text-embedding-3-small"
    COHERE_V3 = "embed-english-v3.0"


class EmbeddingService:
    """
    Service for generating and managing embeddings.
    Supports multiple embedding models and vector databases.
    """
    
    def __init__(
        self,
        model: EmbeddingModel = EmbeddingModel.OPENAI_LARGE,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None
    ) -> None:
        """
        Initialize embedding service.
        
        Args:
            model: Embedding model to use
            qdrant_host: Qdrant host (uses settings if not provided)
            qdrant_port: Qdrant port (uses settings if not provided)
        """
        self.model = model
        self.embedding_client = self._initialize_embedding_client()
        
        # Initialize Qdrant client
        host = qdrant_host or settings.qdrant_host
        port = qdrant_port or settings.qdrant_port
        
        self.qdrant_client = QdrantClient(
            host=host,
            port=port,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None
        )
    
    def _initialize_embedding_client(self) -> Any:
        """Initialize the embedding model client."""
        if self.model in [EmbeddingModel.OPENAI_LARGE, EmbeddingModel.OPENAI_SMALL]:
            return OpenAIEmbeddings(
                model=self.model.value,
                openai_api_key=settings.openai_api_key
            )
        elif self.model == EmbeddingModel.COHERE_V3:
            return CohereEmbeddings(
                model=self.model.value,
                cohere_api_key=settings.cohere_api_key
            )
        else:
            raise ValueError(f"Unsupported embedding model: {self.model}")
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = await self.embedding_client.aembed_query(text)
        return embedding
    
    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            documents: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = await self.embedding_client.aembed_documents(documents)
        return embeddings
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 3072,  # Default for text-embedding-3-large
        distance: Distance = Distance.COSINE
    ) -> bool:
        """
        Create a new collection in Qdrant.
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
            
        Returns:
            True if successful
        """
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            return True
        except Exception as e:
            print(f"Error creating collection: {e}")
            return False
    
    async def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        id_field: str = "id",
        text_field: str = "text"
    ) -> bool:
        """
        Embed and upsert documents into Qdrant collection.
        
        Args:
            collection_name: Target collection name
            documents: List of document dicts with text and metadata
            id_field: Field name for document ID
            text_field: Field name for text content
            
        Returns:
            True if successful
        """
        try:
            # Extract texts for embedding
            texts = [doc[text_field] for doc in documents]
            
            # Generate embeddings
            embeddings = await self.embed_documents(texts)
            
            # Create points for Qdrant
            points = []
            for idx, (doc, embedding) in enumerate(zip(documents, embeddings)):
                point = PointStruct(
                    id=doc.get(id_field, idx),
                    vector=embedding,
                    payload={k: v for k, v in doc.items() if k != text_field}
                )
                points.append(point)
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return True
        except Exception as e:
            print(f"Error upserting documents: {e}")
            return False
    
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in Qdrant collection.
        
        Args:
            collection_name: Collection to search
            query: Search query
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = await self.embed_text(query)
        
        # Search in Qdrant
        search_result = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=filters
        )
        
        # Format results
        results = []
        for hit in search_result:
            results.append({
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload
            })
        
        return results
    
    async def hybrid_search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining dense (semantic) and sparse (keyword) retrieval.
        
        Args:
            collection_name: Collection to search
            query: Search query
            limit: Maximum number of results
            dense_weight: Weight for semantic search
            sparse_weight: Weight for keyword search
            
        Returns:
            List of search results
        """
        # Perform semantic search
        semantic_results = await self.search(
            collection_name=collection_name,
            query=query,
            limit=limit * 2  # Get more results for re-ranking
        )
        
        # TODO: Implement sparse retrieval (BM25) and combine results
        # For now, returning semantic results
        return semantic_results[:limit]
    
    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from Qdrant.
        
        Args:
            collection_name: Name of collection to delete
            
        Returns:
            True if successful
        """
        try:
            self.qdrant_client.delete_collection(collection_name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False


# Helper function to get embedding dimensions
def get_embedding_dimension(model: EmbeddingModel) -> int:
    """
    Get embedding dimension for a model.
    
    Args:
        model: Embedding model
        
    Returns:
        Vector dimension
    """
    dimensions = {
        EmbeddingModel.OPENAI_LARGE: 3072,
        EmbeddingModel.OPENAI_SMALL: 1536,
        EmbeddingModel.COHERE_V3: 1024,
    }
    return dimensions.get(model, 1536)

