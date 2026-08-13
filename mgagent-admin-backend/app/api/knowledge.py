import re
from fastapi import APIRouter, HTTPException, Depends, File, Form, UploadFile, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from urllib.parse import quote
import os
import uuid
import json
import logging
from datetime import datetime
from app.db.database import get_db
from app.db.models import Admin, Document, KnowledgeBase, RetrievalLog, EvalDataset, EvalResult
from .auth import get_current_admin
from app.config.config import get_document_dir
from app.storage import get_storage
from app.rag.vector_factory import get_vector_db

logger = logging.getLogger(__name__)
router = APIRouter()

DOCUMENT_DIR = get_document_dir()


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_files: int
    file_types: Dict[str, int]
    total_size: int
    indexed_count: int
    vector_db_type: str = "milvus"


class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    file_size: int
    created_at: str
    status: str = "indexed"
    document_id: Optional[str] = None
    storage_path: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    document_ids: List[str]


class IndexRequest(BaseModel):
    pass  # 使用全局默认 Embedding 模型，无需前端传参


# 内置 Embedding 模型预设
EMBEDDING_PRESETS = [
    {
        "provider": "openai",
        "name": "OpenAI text-embedding-3-small",
        "model": "text-embedding-3-small",
        "api_base": "https://api.openai.com/v1",
        "dimension": 1536,
        "description": "OpenAI 最新小模型，性价比高，1536维",
        "requires_api_key": True
    },
    {
        "provider": "openai",
        "name": "OpenAI text-embedding-3-large",
        "model": "text-embedding-3-large",
        "api_base": "https://api.openai.com/v1",
        "dimension": 3072,
        "description": "OpenAI 大模型，精度更高，3072维",
        "requires_api_key": True
    },
    {
        "provider": "openai",
        "name": "OpenAI text-embedding-ada-002",
        "model": "text-embedding-ada-002",
        "api_base": "https://api.openai.com/v1",
        "dimension": 1536,
        "description": "OpenAI 经典模型，兼容性好",
        "requires_api_key": True
    },
    {
        "provider": "zhipu",
        "name": "智谱 embedding-3",
        "model": "embedding-3",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "dimension": 2048,
        "description": "智谱 AI 嵌入模型，中文效果好",
        "requires_api_key": True
    },
    {
        "provider": "zhipu",
        "name": "智谱 embedding-2",
        "model": "embedding-2",
        "api_base": "https://open.bigmodel.cn/api/paas/v4",
        "dimension": 1024,
        "description": "智谱 AI 经典嵌入模型",
        "requires_api_key": True
    },
    {
        "provider": "dashscope",
        "name": "通义千问 text-embedding-v3",
        "model": "text-embedding-v3",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "dimension": 1024,
        "description": "阿里通义千问嵌入模型，中文优秀",
        "requires_api_key": True
    },
    {
        "provider": "dashscope",
        "name": "通义千问 text-embedding-v2",
        "model": "text-embedding-v2",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "dimension": 1536,
        "description": "阿里通义千问 v2 嵌入模型",
        "requires_api_key": True
    },
    {
        "provider": "jina",
        "name": "Jina embeddings-v3",
        "model": "jina-embeddings-v3",
        "api_base": "https://api.jina.ai/v1",
        "dimension": 1024,
        "description": "Jina AI 多语言嵌入模型",
        "requires_api_key": True
    },
    {
        "provider": "custom",
        "name": "自定义模型",
        "model": "",
        "api_base": "",
        "dimension": 0,
        "description": "自定义 API 地址和模型名",
        "requires_api_key": True
    },
]


@router.get("/knowledge-base/embedding-presets")
async def get_embedding_presets(admin: Admin = Depends(get_current_admin)):
    """获取内置 Embedding 模型预设列表"""
    return {"presets": EMBEDDING_PRESETS}


@router.get("/knowledge-base/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        documents = db.query(Document).all()
        file_types = {}
        total_size = 0
        indexed_count = 0
        for doc in documents:
            ext = doc.file_type or ""
            file_types[ext] = file_types.get(ext, 0) + 1
            total_size += doc.file_size or 0
            if doc.status == "indexed":
                indexed_count += 1

        vector_db_type = "milvus"

        return KnowledgeBaseStats(
            total_documents=len(documents),
            total_files=len(documents),
            file_types=file_types,
            total_size=total_size,
            indexed_count=indexed_count,
            vector_db_type=vector_db_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents", response_model=List[DocumentInfo])
async def list_documents(admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        documents = db.query(Document).order_by(Document.created_at.desc()).all()
        result = []
        for doc in documents:
            result.append(DocumentInfo(
                filename=doc.filename,
                file_type=doc.file_type,
                file_size=doc.file_size or 0,
                created_at=doc.created_at.isoformat() if doc.created_at else "",
                status=doc.status or "unknown",
                document_id=doc.id,
                storage_path=doc.storage_path
            ))
        return result
    except Exception as e:
        logger.error(f"列出文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_storage_path(document: Document) -> Optional[str]:
    """解析文档的存储路径，兼容旧数据（storage_path 为 NULL 的情况）"""
    if document.storage_path:
        return document.storage_path
    # 旧数据兼容：尝试通过文件名在存储中查找
    storage = get_storage()
    files = storage.list_files()
    for f in files:
        if f.get("name") == document.filename or document.filename in f.get("name", ""):
            return f.get("path") or f.get("name")
    return None


@router.delete("/knowledge-base/documents/{document_id}")
async def delete_document(
    document_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档记录不存在")

        storage_path = document.storage_path or _resolve_storage_path(document)
        storage = get_storage()

        # 从存储删除文件
        if storage_path and storage.exists(storage_path):
            storage.delete(storage_path)

        # 从向量数据库删除对应的 chunks
        try:
            vector_db = get_vector_db()
            chunks = vector_db.get_all_chunks()
            ids_to_delete = [
                chunk["id"] for chunk in chunks
                if chunk.get("metadata", {}).get("document_id") == document_id
            ]
            if ids_to_delete:
                vector_db.delete_by_ids(ids_to_delete)
        except Exception as vec_err:
            logger.warning(f"向量数据删除失败: {vec_err}")

        # 删除数据库记录
        db.delete(document)
        db.commit()
        return {"message": f"文档 {document.filename} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/documents/batch-delete")
async def batch_delete_documents(
    request: BatchDeleteRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        deleted = []
        failed = []
        storage = get_storage()

        for doc_id in request.document_ids:
            document = db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                failed.append({"id": doc_id, "reason": "记录不存在"})
                continue

            storage_path = document.storage_path or _resolve_storage_path(document)
            if storage_path and storage.exists(storage_path):
                storage.delete(storage_path)

            try:
                vector_db = get_vector_db()
                chunks = vector_db.get_all_chunks()
                ids_to_delete = [
                    chunk["id"] for chunk in chunks
                    if chunk.get("metadata", {}).get("document_id") == doc_id
                ]
                if ids_to_delete:
                    vector_db.delete_by_ids(ids_to_delete)
            except Exception as vec_err:
                logger.warning(f"向量数据删除失败 (doc={doc_id}): {vec_err}")

            db.delete(document)
            deleted.append(doc_id)

        db.commit()
        return {"deleted": deleted, "failed": failed, "message": f"已删除 {len(deleted)} 个文档"}
    except Exception as e:
        logger.error(f"批量删除失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents/{document_id}/download")
async def download_document(
    document_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档记录不存在")

        storage_path = document.storage_path or _resolve_storage_path(document)
        if not storage_path:
            raise HTTPException(status_code=404, detail="文件存储路径不存在，请重新上传文档")

        storage = get_storage()
        if not storage.exists(storage_path):
            raise HTTPException(status_code=404, detail="文件不存在于存储中")

        file_data = storage.download(storage_path)

        # 使用 RFC 5987 编码处理中文文件名，避免 UnicodeEncodeError
        encoded_filename = quote(document.filename)
        return Response(
            content=file_data,
            media_type='application/octet-stream',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
                'Content-Length': str(len(file_data))
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents/{document_id}/preview")
async def preview_document(
    document_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档记录不存在")

        storage_path = document.storage_path or _resolve_storage_path(document)
        if not storage_path:
            raise HTTPException(status_code=404, detail="文件存储路径不存在，请重新上传文档")

        storage = get_storage()
        if not storage.exists(storage_path):
            raise HTTPException(status_code=404, detail="文件不存在于存储中")

        file_data = storage.download(storage_path)
        file_ext = document.file_type or os.path.splitext(document.filename)[1].lower()

        # 写入临时文件用于预览
        temp_dir = get_document_dir()
        temp_file_path = temp_dir / f"preview_{uuid.uuid4()}{file_ext}"
        with open(temp_file_path, "wb") as f:
            f.write(file_data)

        try:
            if file_ext in (".txt", ".md"):
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content, "type": "text"}

            elif file_ext == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(str(temp_file_path))
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text() or ""
                    return {"content": content[:5000], "type": "text", "truncated": len(content) > 5000}
                except Exception as pdf_err:
                    return {"content": f"PDF预览失败: {str(pdf_err)}", "type": "error"}

            elif file_ext == ".docx":
                try:
                    import docx2txt
                    content = docx2txt.process(str(temp_file_path))
                    return {"content": content[:5000], "type": "text", "truncated": len(content) > 5000}
                except ImportError:
                    return {"content": "需要安装 docx2txt 才能预览 DOCX 文件", "type": "error"}

            else:
                return {"content": f"不支持预览 {file_ext} 格式的文件", "type": "error"}
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/upload")
async def upload_knowledge_base_document(
    file: UploadFile = File(...),
    knowledge_base_id: Optional[str] = Form(None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """上传文档到知识库（仅上传文件，不自动索引）"""
    try:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md", ".csv", ".json", ".py", ".js", ".java", ".ts", ".go", ".html"]
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")

        file_data = await file.read()
        file_size = len(file_data)

        # 创建 Document 记录
        document_id = str(uuid.uuid4())
        document = Document(
            id=document_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            storage_path=None,
            status="uploaded",
            tenant_id=admin.tenant_id,
            knowledge_base_id=knowledge_base_id,
            created_at=datetime.utcnow()
        )
        if not knowledge_base_id:
            # Auto-create or reuse Default KB for backward compat
            from app.db.models import KnowledgeBase as _KB
            default = db.query(_KB).filter(_KB.name == "Default").first()
            if not default:
                import uuid as _u
                default = _KB(
                    id=str(_u.uuid4()), name="Default",
                    description="默认知识库 - 自动迁移历史文档至此",
                    vector_db_type="default",
                    chunk_size=500, chunk_overlap=50,
                    retrieve_limit=5, enable_hybrid=False, hybrid_alpha=0.7,
                    is_active=True,
                )
                db.add(default); db.commit(); db.refresh(default)
            document.knowledge_base_id = default.id
        db.add(document)
        db.commit()

        # 上传到存储
        try:
            storage = get_storage()
            stored_path = storage.upload(file.filename, file_data)
            document.storage_path = stored_path
            db.commit()
        except Exception as storage_err:
            document.status = "error"
            db.commit()
            raise HTTPException(status_code=500, detail=f"文件存储失败: {str(storage_err)}")

        db.refresh(document)
        return {
            "message": f"文档 {file.filename} 上传成功",
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_ext,
            "file_size": file_size,
            "status": "uploaded"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/documents/{document_id}/index")
async def index_document(
    document_id: str,
    force: bool = False,
    request: Optional[IndexRequest] = None,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """将已上传的文档加载到向量数据库（索引化）"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档记录不存在")

        if document.status == "indexed" and not force:
            return {"message": "文档已索引，无需重复操作（传 ?force=true 强制重建）", "document_id": document_id, "force_reindex_hint": "传 ?force=true 强制重建"}
        if force and document.chunk_ids:
            try:
                ids = json.loads(document.chunk_ids)
                if ids:
                    vdb = get_vector_db()
                    vdb.delete_by_ids(ids)
            except Exception:
                pass

        storage_path = document.storage_path or _resolve_storage_path(document)
        if not storage_path:
            raise HTTPException(status_code=400, detail="文件存储路径不存在，请重新上传文档")

        storage = get_storage()
        if not storage.exists(storage_path):
            raise HTTPException(status_code=400, detail="文件不存在于存储中，请重新上传")

        # 更新状态为索引中
        document.status = "indexing"
        db.commit()

        file_ext = document.file_type or os.path.splitext(document.filename)[1].lower()
        temp_dir = get_document_dir()
        temp_file_path = temp_dir / f"index_{uuid.uuid4()}{file_ext}"

        try:
            # 从存储下载文件
            content = storage.download(storage_path)
            with open(temp_file_path, "wb") as f:
                f.write(content)

            from langchain_community.document_loaders import PyPDFLoader, TextLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            import docx2txt

            docs = []
            if file_ext == ".pdf":
                loader = PyPDFLoader(str(temp_file_path))
                docs = loader.load()
            elif file_ext == ".docx":
                text = docx2txt.process(str(temp_file_path))
                docs = [{"page_content": text, "metadata": {"source": storage_path, "document_id": document_id}}]
            elif file_ext == ".md":
                loader = TextLoader(str(temp_file_path))
                docs = loader.load()
            else:
                loader = TextLoader(str(temp_file_path))
                docs = loader.load()

            # 为所有文档块添加 document_id
            if file_ext != ".docx":
                for doc in docs:
                    if hasattr(doc, 'metadata'):
                        doc.metadata['document_id'] = document_id
                        doc.metadata['source'] = storage_path

            chunk_size_val = 500
            chunk_overlap_val = 50
            if document.knowledge_base_id:
                _kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == document.knowledge_base_id).first()
                if _kb:
                    chunk_size_val = _kb.chunk_size or 500
                    chunk_overlap_val = _kb.chunk_overlap or 50
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size_val,
                chunk_overlap=chunk_overlap_val,
                length_function=len
            )

            if isinstance(docs[0], dict):
                texts = splitter.create_documents([docs[0]["page_content"]])
                for text in texts:
                    if hasattr(text, 'metadata'):
                        text.metadata['document_id'] = document_id
                        text.metadata['source'] = storage_path
                    else:
                        text.metadata = {'document_id': document_id, 'source': storage_path}
            else:
                texts = splitter.split_documents(docs)

            # 生成真实向量 - 使用全局默认 Embedding 模型
            try:
                from app.services.model_config_service import get_embeddings_model

                embeddings_model = get_embeddings_model(db)
                text_contents = [t.page_content if hasattr(t, 'page_content') else str(t) for t in texts]
                embeddings = embeddings_model.embed_documents(text_contents)
            except ValueError as e:
                document.status = "error"
                db.commit()
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as emb_err:
                document.status = "error"
                db.commit()
                raise HTTPException(
                    status_code=500,
                    detail=f"生成向量嵌入失败: {str(emb_err)}"
                )

            vector_db = get_vector_db()
            # Tag chunks with knowledge_base_id for isolation
            for t in texts:
                if hasattr(t, 'metadata'):
                    t.metadata['knowledge_base_id'] = document.knowledge_base_id
            vector_db.add_documents(texts, embeddings)

            # Track chunk IDs for future force-reindex cleanup
            document.chunk_ids = json.dumps([
                getattr(t, 'metadata', {}).get('chunk_id', f"{document.id}_{i}")
                for i, t in enumerate(texts)
            ])
            document.status = "indexed"
            db.commit()

            # 获取当前 Embedding 模型信息用于返回
            from app.services.model_config_service import get_active_embedding_config
            emb_config = get_active_embedding_config(db)
            emb_model_name = emb_config.get("model_name", "") if emb_config else "unknown"

            return {
                "message": f"文档 {document.filename} 索引成功",
                "document_id": document_id,
                "chunks_count": len(texts),
                "status": "indexed",
                "embedding_model": emb_model_name
            }
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        # 恢复状态为已上传
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "uploaded"
            db.commit()
        logger.error(f"索引文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# P0/P1/P2: Complete Knowledge Base management
# All routes appended here to avoid interfering with existing route order
# ============================================================================

# ---- Helpers ----

def _ensure_default_kb(db_s):
    default = db_s.query(KnowledgeBase).filter(KnowledgeBase.name == "Default").first()
    if not default:
        import uuid as _u
        default = KnowledgeBase(
            id=str(_u.uuid4()), name="Default",
            description="默认知识库 - 自动迁移历史文档至此",
            vector_db_type="default",
            chunk_size=500, chunk_overlap=50,
            retrieve_limit=5, enable_hybrid=False, hybrid_alpha=0.7,
            is_active=True,
        )
        db_s.add(default); db_s.commit(); db_s.refresh(default)
    return default


def _kb_to_dict(kb, db_s) -> dict:
    cnt = db_s.query(Document).filter(Document.knowledge_base_id == kb.id).count()
    return {
        "id": kb.id, "name": kb.name, "description": kb.description,
        "tenant_id": kb.tenant_id, "vector_db_type": kb.vector_db_type,
        "embedding_model_id": kb.embedding_model_id,
        "chunk_size": kb.chunk_size, "chunk_overlap": kb.chunk_overlap,
        "chunk_separator": kb.chunk_separator,
        "retrieve_limit": kb.retrieve_limit,
        "similarity_threshold": kb.similarity_threshold,
        "enable_rerank": kb.enable_rerank,
        "rerank_model_id": kb.rerank_model_id,
        "rerank_top_n": kb.rerank_top_n,
        "rerank_score_threshold": kb.rerank_score_threshold,
        "enable_hybrid": kb.enable_hybrid, "hybrid_alpha": kb.hybrid_alpha,
        "is_active": kb.is_active,
        "created_at": kb.created_at.isoformat() if kb.created_at else None,
        "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
        "document_count": cnt,
    }


# ---- Schemas ----

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    vector_db_type: Optional[str] = "default"
    embedding_model_id: Optional[str] = None
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 50
    chunk_separator: Optional[str] = None
    retrieve_limit: Optional[int] = 5
    similarity_threshold: Optional[float] = None
    enable_rerank: Optional[bool] = False
    rerank_model_id: Optional[str] = None
    rerank_top_n: Optional[int] = 3
    rerank_score_threshold: Optional[float] = None
    enable_hybrid: Optional[bool] = False
    hybrid_alpha: Optional[float] = 0.7
    is_active: Optional[bool] = True


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    vector_db_type: Optional[str] = None
    embedding_model_id: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunk_separator: Optional[str] = None
    retrieve_limit: Optional[int] = None
    similarity_threshold: Optional[float] = None
    enable_rerank: Optional[bool] = None
    rerank_model_id: Optional[str] = None
    rerank_top_n: Optional[int] = None
    rerank_score_threshold: Optional[float] = None
    enable_hybrid: Optional[bool] = None
    hybrid_alpha: Optional[float] = None
    is_active: Optional[bool] = None


class RetrieveTestRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = None
    enable_hybrid: Optional[bool] = None
    hybrid_alpha: Optional[float] = None
    enable_rerank: Optional[bool] = None
    rerank_top_n: Optional[int] = None


class EvalDatasetItemCreate(BaseModel):
    query: str
    expected_document_ids: List[str] = []
    name: Optional[str] = None


class RunEvalRequest(BaseModel):
    top_k: Optional[int] = 10


# ---- P0: Static routes (MUST come before /{kb_id} param route) ----

@router.get("/knowledge-base/list")
async def api_list_knowledge_bases(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_default_kb(db)
    kbs = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()
    return {"items": [_kb_to_dict(k, db) for k in kbs]}


@router.get("/knowledge-base/retrieve-logs")
async def list_retrieve_logs(
    limit: int = Query(default=50, ge=1, le=500),
    knowledge_base_id: Optional[str] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        q = db.query(RetrievalLog)
        if knowledge_base_id:
            q = q.filter(RetrievalLog.knowledge_base_id == knowledge_base_id)
        logs = q.order_by(RetrievalLog.created_at.desc()).limit(limit).all()
        return [
            {
                "id": l.id, "query": l.query,
                "knowledge_base_id": l.knowledge_base_id, "kb_name": l.kb_name,
                "top_k": l.top_k, "threshold_applied": l.threshold_applied,
                "threshold_value": l.threshold_value,
                "results_count": l.results_count,
                "rerank_applied": l.rerank_applied,
                "hybrid_applied": l.hybrid_applied,
                "latency_ms": l.latency_ms,
                "results_preview": (l.results_json or "")[:200],
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    except Exception as e:
        logger.error(f"列出检索日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---- P0: Param routes (/{kb_id}) ----

@router.get("/knowledge-base/{kb_id}")
async def api_get_knowledge_base(kb_id: str, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return _kb_to_dict(kb, db)


@router.post("/knowledge-base")
async def api_create_knowledge_base(
    data: KnowledgeBaseCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    payload = data.model_dump(exclude_unset=True)
    payload["id"] = str(uuid.uuid4())
    payload["tenant_id"] = admin.tenant_id
    try:
        kb = KnowledgeBase(**payload)
        db.add(kb); db.commit(); db.refresh(kb)
        return _kb_to_dict(kb, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"创建知识库失败: {str(e)}")


@router.put("/knowledge-base/{kb_id}")
async def api_update_knowledge_base(
    kb_id: str,
    data: KnowledgeBaseUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(kb, k, v)
    db.commit(); db.refresh(kb)
    return _kb_to_dict(kb, db)


@router.delete("/knowledge-base/{kb_id}")
async def api_delete_knowledge_base(
    kb_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if kb.name == "Default":
        raise HTTPException(status_code=400, detail="Default 不可删除")
    default = _ensure_default_kb(db)
    for d in db.query(Document).filter(Document.knowledge_base_id == kb_id).all():
        d.knowledge_base_id = default.id
    db.delete(kb); db.commit()
    return {"message": f"知识库已删除，{kb.name} 文档已迁移到 Default"}


# ---- P1: Retrieve Test ----

@router.post("/knowledge-base/{kb_id}/retrieve-test")
async def retrieve_test(
    kb_id: str,
    payload: RetrieveTestRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    import time as _t
    t0 = _t.time()
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    from app.services.model_config_service import get_embeddings_model
    try:
        emb_model = get_embeddings_model(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    top_k = payload.top_k or kb.retrieve_limit or 5
    query_emb = emb_model.embed_query(payload.query)
    vector_db = get_vector_db()

    results = vector_db.similarity_search(
        query_emb, top_k * 3,
        knowledge_base_ids=[kb_id],
    )

    # Hybrid BM25
    hybrid_executed = False
    if (payload.enable_hybrid if payload.enable_hybrid is not None else kb.enable_hybrid):
        try:
            try:
                from app.rag.retriever import _extract_keywords
                kw_list = _extract_keywords(payload.query)
            except ImportError:
                kw_list = [w for w in re.findall(r"[\w\u4e00-\u9fff]+", payload.query) if w.strip()]
            kw = vector_db.keyword_search(kw_list, top_k * 3,
                                          knowledge_base_ids=[kb_id])
            seen = {}
            for rank, r in enumerate(results):
                cid = r.get("id", "")
                seen[cid] = {"result": r, "score": seen.get(cid, (0, None))[0] + 1.0 / (60 + rank + 1)}
            for rank, r in enumerate(kw):
                cid = r.get("id", "")
                prev = seen.get(cid, (0, None))
                seen[cid] = {"result": r, "score": prev[0] + 1.0 / (60 + rank + 1)}
            fused = sorted(seen.values(), key=lambda x: x["score"], reverse=True)
            results = [v["result"] for v in fused[:top_k * 3]]
            hybrid_executed = True
        except Exception as he:
            logger.warning(f"Hybrid keyword failed: {he}")

    # Similarity threshold
    thresh_applied = False
    thresh_val = payload.similarity_threshold
    if thresh_val is None:
        thresh_val = kb.similarity_threshold
    if thresh_val is not None:
        filtered = []
        for r in results:
            dist = r.get("distance", r.get("score", 1.0))
            if dist <= thresh_val:
                filtered.append(r)
        results = filtered
        thresh_applied = True

    results = results[:top_k]

    # Rerank
    rerank_executed = False
    rerank_top_n = payload.rerank_top_n or kb.rerank_top_n or 3
    if (payload.enable_rerank if payload.enable_rerank is not None else kb.enable_rerank) and len(results) > 1:
        try:
            from app.services.reranker_factory import get_reranker
            reranker = get_reranker(db, kb.rerank_model_id)
            pairs = [(payload.query, r.get("content", r.get("text", ""))) for r in results]
            scores = reranker.rerank(pairs)
            for r, s in zip(results, scores):
                r["rerank_score"] = s
            results.sort(key=lambda r: r.get("rerank_score", 0), reverse=True)
            results = results[:rerank_top_n]
            rerank_executed = True
        except Exception as re:
            logger.warning(f"Rerank failed: {re}")

    latency_ms = round((_t.time() - t0) * 1000, 1)

    # Log
    try:
        log = RetrievalLog(
            knowledge_base_id=kb_id, kb_name=kb.name,
            query=payload.query, top_k=top_k,
            threshold_applied=thresh_applied, threshold_value=thresh_val,
            results_count=len(results),
            rerank_applied=rerank_executed, hybrid_applied=hybrid_executed,
            latency_ms=latency_ms,
            results_json=json.dumps([{
                "content": (r.get("content") or r.get("text") or "")[:200],
                "metadata": r.get("metadata", {}),
                "distance": r.get("distance"), "score": r.get("score"),
            } for r in results], ensure_ascii=False),
        )
        db.add(log); db.commit()
    except Exception as le:
        logger.warning(f"Log write failed: {le}")

    return {
        "query": payload.query,
        "knowledge_base": _kb_to_dict(kb, db),
        "chunks": [{
            "id": r.get("id"),
            "content": r.get("content") or r.get("text", ""),
            "metadata": r.get("metadata", {}),
            "distance": r.get("distance"),
            "score": r.get("score"),
            "rerank_score": r.get("rerank_score"),
        } for r in results],
        "hybrid_executed": hybrid_executed,
        "rerank_executed": rerank_executed,
        "threshold_applied": thresh_applied,
        "latency_ms": latency_ms,
        "timings_ms": {"total": latency_ms},
        "note": "完整管线已执行",
    }


# ---- P2: Eval Dataset CRUD ----

@router.get("/knowledge-base/{kb_id}/eval-dataset")
async def list_eval_dataset(kb_id: str, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    items = db.query(EvalDataset).filter(EvalDataset.knowledge_base_id == kb_id).all()
    return [{
        "id": i.id, "query": i.query,
        "expected_document_ids": json.loads(i.expected_document_ids or "[]"),
        "created_at": i.created_at.isoformat() if i.created_at else None,
    } for i in items]


@router.post("/knowledge-base/{kb_id}/eval-dataset")
async def add_eval_dataset_item(
    kb_id: str, item: EvalDatasetItemCreate,
    admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    auto_name = item.name or (item.query[:50] + ("..." if len(item.query) > 50 else "")) or f"eval-{uuid.uuid4().hex[:8]}"
    e = EvalDataset(
        knowledge_base_id=kb_id, name=auto_name, query=item.query,
        expected_document_ids=json.dumps(item.expected_document_ids or [], ensure_ascii=False),
    )
    db.add(e); db.commit(); db.refresh(e)
    return {"id": e.id, "message": "添加成功"}


@router.delete("/knowledge-base/{kb_id}/eval-dataset/{item_id}")
async def delete_eval_item(
    kb_id: str, item_id: int,
    admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    item = db.query(EvalDataset).filter(
        EvalDataset.id == item_id, EvalDataset.knowledge_base_id == kb_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="评估集条目不存在")
    db.delete(item); db.commit()
    return {"message": "删除成功"}


# ---- P2: Run Eval ----

@router.post("/knowledge-base/{kb_id}/eval")
async def run_eval(
    kb_id: str,
    req: Optional[RunEvalRequest] = None,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    import time as _t
    t0 = _t.time()
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    dataset = db.query(EvalDataset).filter(EvalDataset.knowledge_base_id == kb_id).all()
    if not dataset:
        raise HTTPException(status_code=400, detail="该知识库没有评估数据集，请先添加")

    top_k = req.top_k if req else 10
    from app.services.model_config_service import get_embeddings_model
    try:
        emb_model = get_embeddings_model(db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    vdb = get_vector_db()
    total = len(dataset)
    hits = {1: 0, 3: 0, 5: 0, 10: 0}
    rr_sum = {5: 0.0, 10: 0.0}

    for entry in dataset:
        try:
            emb = emb_model.embed_query(entry.query)
        except Exception:
            continue
        results = vdb.similarity_search(
            emb, top_k * 2, knowledge_base_ids=[kb_id])
        rel_ids = set(json.loads(entry.expected_document_ids or "[]"))
        ranks = []
        for i, r in enumerate(results[:top_k], 1):
            did = r.get("metadata", {}).get("document_id")
            if did in rel_ids and i not in ranks:
                ranks.append(i)
        for k in hits:
            if any(r <= k for r in ranks):
                hits[k] += 1
        for k in rr_sum:
            r = next((x for x in ranks if x <= k), None)
            if r:
                rr_sum[k] += 1.0 / r

    hit_rate = {f"at_{k}": round(hits[k] / total, 4) if total else 0.0 for k in hits}
    mrr = {f"at_{k}": round(rr_sum[k] / total, 4) if total else 0.0 for k in rr_sum}
    latency_ms = round((_t.time() - t0) * 1000, 1)

    result = EvalResult(
        knowledge_base_id=kb_id,
        config_snapshot=json.dumps({
            "chunk_size": kb.chunk_size, "chunk_overlap": kb.chunk_overlap,
            "similarity_threshold": kb.similarity_threshold,
            "enable_hybrid": kb.enable_hybrid, "hybrid_alpha": kb.hybrid_alpha,
            "enable_rerank": kb.enable_rerank, "rerank_top_n": kb.rerank_top_n,
        }, ensure_ascii=False),
        total_queries=total,
        hit_at_1=hits[1], hit_at_3=hits[3], hit_at_5=hits[5], hit_at_10=hits[10],
        mrr_at_5=rr_sum[5] / total if total else 0.0,
        mrr_at_10=rr_sum[10] / total if total else 0.0,
        latency_ms=latency_ms,
    )
    db.add(result); db.commit(); db.refresh(result)

    return {
        "eval_result_id": result.id,
        "knowledge_base": kb.name,
        "total_queries": total,
        "hit_rate": hit_rate, "mrr": mrr,
        "latency_ms": latency_ms,
        "config": json.loads(result.config_snapshot or "{}"),
    }


# ---- P2: Eval Results ----

@router.get("/knowledge-base/{kb_id}/eval-results")
async def list_eval_results(
    kb_id: str, admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    results = db.query(EvalResult).filter(EvalResult.knowledge_base_id == kb_id)\
        .order_by(EvalResult.created_at.desc()).limit(50).all()
    return [{
        "id": r.id, "knowledge_base_id": r.knowledge_base_id,
        "total_queries": r.total_queries,
        "hit_at_1": r.hit_at_1, "hit_at_3": r.hit_at_3,
        "hit_at_5": r.hit_at_5, "hit_at_10": r.hit_at_10,
        "mrr_at_5": r.mrr_at_5, "mrr_at_10": r.mrr_at_10,
        "latency_ms": r.latency_ms,
        "config": json.loads(r.config_snapshot or "{}"),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in results]
