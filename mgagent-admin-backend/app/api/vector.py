from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db.models import Admin
from .auth import get_current_admin
from app.config.settings import CHROMA_DIR

router = APIRouter()

class VectorDBStats(BaseModel):
    total_chunks: int
    persist_directory: str
    embedding_model: str

class VectorChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]

@router.get("/vector-db/stats", response_model=VectorDBStats)
async def get_vector_db_stats(admin: Admin = Depends(get_current_admin)):
    try:
        from langchain_chroma import Chroma
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        total_chunks = chroma_client._collection.count()
        
        return VectorDBStats(
            total_chunks=total_chunks,
            persist_directory=str(CHROMA_DIR),
            embedding_model="TF-IDF Embeddings"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-db/chunks", response_model=List[VectorChunk])
async def list_vector_chunks(
    limit: int = Query(10),
    offset: int = Query(0),
    admin: Admin = Depends(get_current_admin)
):
    try:
        from langchain_chroma import Chroma
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        results = chroma_client._collection.get(
            limit=limit,
            offset=offset,
            include=["documents", "metadatas", "embeddings"]
        )
        
        chunks = []
        for i, (doc_id, content, metadata) in enumerate(zip(
            results["ids"],
            results["documents"],
            results["metadatas"]
        )):
            chunks.append(VectorChunk(
                id=doc_id,
                content=content,
                metadata=metadata
            ))
        
        return chunks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-db/search")
async def search_vector_db(
    query: str,
    k: int = Query(3),
    admin: Admin = Depends(get_current_admin)
):
    try:
        from langchain_chroma import Chroma
        from langchain_openai import OpenAIEmbeddings
        
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        
        results = chroma_client.similarity_search_with_score(query, k=k)
        
        search_results = []
        for doc, score in results:
            search_results.append({
                "id": doc.metadata.get("id", str(hash(doc.page_content))),
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": float(1 - score)
            })
        
        if not search_results:
            return {"results": [], "message": "未找到匹配的结果"}
        
        return {"results": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/vector-db/chunks/{chunk_id}")
async def delete_vector_chunk(chunk_id: str, admin: Admin = Depends(get_current_admin)):
    try:
        from langchain_chroma import Chroma
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        chroma_client._collection.delete(ids=[chunk_id])
        
        return {"message": f"向量块 {chunk_id} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vector-db/clear")
async def clear_vector_db(admin: Admin = Depends(get_current_admin)):
    try:
        from langchain_chroma import Chroma
        
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        
        # 获取所有向量块的ID
        all_chunks = chroma_client._collection.get(include=["documents"])
        if all_chunks["ids"]:
            chroma_client._collection.delete(ids=all_chunks["ids"])
        
        return {"message": "向量数据库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
