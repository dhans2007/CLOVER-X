import os
import faiss
import pdfplumber
import docx
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize the embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

class RAGPipeline:
    def __init__(self, chunk_size=400, overlap=50, similarity_threshold=0.3):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.similarity_threshold = similarity_threshold
        
        self.index = None
        self.chunks = []

    def extract_text(self, filepath: str) -> str:
        """Extracts text based on file extension."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".pdf":
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        elif ext == ".docx":
            doc = docx.Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError("Unsupported file format.")

    def split_text(self, text: str) -> list[str]:
        """Splits text into chunks using naive word boundaries with overlap."""
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
            if i + self.chunk_size >= len(words):
                break
            i += self.chunk_size - self.overlap
        return chunks

    def process_document(self, filepath: str):
        """Extracts text, splits it, embeds chunks, and builds FAISS index."""
        text = self.extract_text(filepath)
        if not text.strip():
            raise ValueError("The uploaded document is empty or could not be read.")
            
        self.chunks = self.split_text(text)
        
        # Generate embeddings
        embeddings = embedding_model.encode(self.chunks)
        
        # Convert to numpy array of float32
        embeddings = np.array(embeddings).astype('float32')
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

    def retrieve(self, query: str, top_k=3) -> list[str]:
        """Retrieves top_k chunks based on semantic similarity."""
        if self.index is None or not self.chunks:
            return []
            
        query_embedding = embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, top_k)
        
        retrieved_chunks = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                distance = distances[0][i]
                if distance < self.similarity_threshold * 10: # Rough approximation
                    retrieved_chunks.append(self.chunks[idx])
                    
        return retrieved_chunks

# Global instance for the single document use-case
rag_instance = RAGPipeline(similarity_threshold=0.8) # Adjusted threshold for L2
