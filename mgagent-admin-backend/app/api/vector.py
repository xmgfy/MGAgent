"""
向量数据库管理接口 - 支持双方案（ChromaDB / Milvus）
嵌入模型从数据库配置获取，无兜底逻辑
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db.models import Admin
from .auth import get_current_admin
from app.config.config import is_mysql_scheme, settings
from app.rag.vector_factory import get_vector_db
from app.services.model_config_service import get_embeddings_model

router = APIRouter()


class VectorDBStats(BaseModel):
    total_chunks: int
    vector_db_type: str
    host: str = ""
    port: str = ""
    collection_name: str = ""
    persist_directory: str = ""
    embedding_model: str = ""


class VectorChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]


@router.get("/vector-db/stats", response_model=VectorDBStats)
async def get_vector_db_stats(admin: Admin = Depends(get_current_admin)):
    """获取向量数据库统计信息"""
    try:
        vector_db = get_vector_db()
        total_chunks = vector_db.get_total_count()
        
        # 获取嵌入模型信息
        embeddings = get_embeddings_model()
        embedding_model_name = type(embeddings).__name__
        
        if is_mysql_scheme():
            return VectorDBStats(
                total_chunks=total_chunks,
                vector_db_type="milvus",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                collection_name=settings.MILVUS_COLLECTION,
                embedding_model=embedding_model_name
            )
        else:
            from app.config.config import get_chroma_dir
            return VectorDBStats(
                total_chunks=total_chunks,
                vector_db_type="chromadb",
                persist_directory=str(get_chroma_dir()),
                collection_name="mgagent_knowledge",
                embedding_model=embedding_model_name
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector-db/chunks", response_model=List[VectorChunk])
async def list_vector_chunks(
    limit: int = Query(50),
    offset: int = Query(0),
    admin: Admin = Depends(get_current_admin)
):
    """列出向量块"""
    try:
        vector_db = get_vector_db()
        all_chunks = vector_db.get_all_chunks()
        
        # 分页
        paginated_chunks = all_chunks[offset:offset + limit]
        
        chunks = []
        for chunk in paginated_chunks:
            chunks.append(VectorChunk(
                id=chunk["id"],
                content=chunk.get("content", ""),
                metadata=chunk.get("metadata", {})
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
    """搜索向量数据库，使用配置的嵌入模型"""
    try:
        vector_db = get_vector_db()
        
        # 使用配置的嵌入模型生成查询嵌入
        embeddings = get_embeddings_model()
        query_embedding = embeddings.embed_query(query)
        
        # 搜索
        results = vector_db.similarity_search(query_embedding, k=k)
        
        search_results = []
        for result in results:
            search_results.append({
                "id": result["id"],
                "content": result["content"],
                "metadata": result["metadata"],
                "similarity": float(1 - result.get("distance", 0))
            })
        
        if not search_results:
            return {"results": [], "message": "未找到匹配的结果"}
        
        return {"results": search_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/vector-db/chunks/{chunk_id}")
async def delete_vector_chunk(chunk_id: str, admin: Admin = Depends(get_current_admin)):
    """删除单个向量块"""
    try:
        vector_db = get_vector_db()
        vector_db.delete_by_ids([chunk_id])
        
        return {"message": f"向量块 {chunk_id} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector-db/clear")
async def clear_vector_db(admin: Admin = Depends(get_current_admin)):
    """清空向量数据库"""
    try:
        vector_db = get_vector_db()
        vector_db.clear_all()
        
        return {"message": "向量数据库已清空并重新初始化"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
