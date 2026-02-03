import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import os
from typing import List, Dict, Any

class RAGManager:
    """
    Manages Retrieval Augmented Generation (RAG) pipeline.
    - Stores knowledge in a local Vector Database (ChromaDB)
    - Retrieves relevant context for the Orchestrator
    """
    
    def __init__(self, persistence_path: str = "./backend/brain/data"):
        """
        Initialize the Vector DB and Embedding Model.
        """
        # Ensure data directory exists
        os.makedirs(persistence_path, exist_ok=True)
        
        print("🧠 Loading RAG Engine...")
        
        # 1. Initialize Vector DB (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(path=persistence_path)
        
        # 2. Initialize Neural Network for Embeddings
        # 'all-MiniLM-L6-v2' is fast, lightweight, and effective for local use.
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 3. Get or Create Collections
        self.book_collection = self.chroma_client.get_or_create_collection("books")
        self.rules_collection = self.chroma_client.get_or_create_collection("rules")
        
        print("✅ RAG Engine Ready.")

    def add_book_to_memory(self, book_id: str, title: str, author: str, description: str, category: str):
        """
        Embeds a book and saves it to the vector store.
        """
        # Create a rich textual representation for embedding
        text_to_embed = f"{title} by {author}. Category: {category}. Description: {description}"
        
        # Add to ChromaDB (it will handle embedding automatically if we didn't use a custom encoder, 
        # but manual encoding is often more stable across environments).
        # Actually, let's use the built-in embedding function of Chroma or our own.
        # For control, we'll embed manually or just pass text if using default.
        # Let's pass text and let Chroma's default or our SentenceTransformer handle it.
        # To keep it simple, we'll generate embeddings manually.
        
        embedding = self.encoder.encode(text_to_embed).tolist()
        
        self.book_collection.upsert(
            documents=[text_to_embed],
            embeddings=[embedding],
            metadatas=[{
                "book_id": book_id, 
                "title": title, 
                "author": author, 
                "category": category
            }],
            ids=[str(book_id)]
        )

    def search_books(self, query: str, n_results: int = 3):
        """
        Semantic search for books based on a user query.
        """
        query_embedding = self.encoder.encode(query).tolist()
        
        results = self.book_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Chroma returns lists of lists. Flatten for easier consumption.
        # results['metadatas'][0] contains the list of metadata dicts
        return results['metadatas'][0] if results['metadatas'] else []

# Singleton instance
rag = RAGManager()
