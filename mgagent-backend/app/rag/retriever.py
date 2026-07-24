from langchain_chroma import Chroma
from langchain_core.documents import Document
from typing import List, Optional
from app.config.settings import CHROMA_DIR

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain.embeddings.base import Embeddings
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class TfidfEmbeddings(Embeddings):
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b\w+\b"
        )
        self.fitted = False
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.fitted:
            self.vectorizer.fit(texts)
            self.fitted = True
        return self.vectorizer.transform(texts).toarray().tolist()
    
    def embed_query(self, text: str) -> List[float]:
        if not self.fitted:
            self.vectorizer.fit([text])
            self.fitted = True
        return self.vectorizer.transform([text]).toarray()[0].tolist()

class VectorRetriever:
    def __init__(self):
        from app.config.settings import settings
        
        use_local_embedding = settings.OPENAI_API_BASE and "deepseek" in settings.OPENAI_API_BASE.lower()
        
        if use_local_embedding or not OPENAI_AVAILABLE:
            if SKLEARN_AVAILABLE:
                self.embeddings = TfidfEmbeddings()
            else:
                raise ImportError("请安装 scikit-learn")
        else:
            try:
                self.embeddings = OpenAIEmbeddings(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
            except Exception:
                if SKLEARN_AVAILABLE:
                    self.embeddings = TfidfEmbeddings()
                else:
                    raise ImportError("请安装 scikit-learn")
        
        self.vector_store = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=self.embeddings
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        if not documents:
            return []
        return self.vector_store.add_documents(documents)
    
    def get_retriever(self, k: int = 3, search_type: str = "similarity"):
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
    
    def search(self, query: str, k: int = 3) -> List[Document]:
        retriever = self.get_retriever(k=k)
        try:
            return retriever.get_relevant_documents(query)
        except AttributeError:
            return retriever.invoke(query)
    
    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        return self.vector_store.similarity_search(query, k=k)
    
    def delete_by_ids(self, ids: List[str]) -> None:
        self.vector_store.delete(ids=ids)
    
    def get_collection_stats(self) -> dict:
        return {
            "total_documents": self.vector_store._collection.count(),
            "persist_directory": str(CHROMA_DIR),
            "embedding_model": type(self.embeddings).__name__
        }
    
    def clear_all(self) -> None:
        self.vector_store._collection.delete(where={})

vector_retriever = VectorRetriever()