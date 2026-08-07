from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from urllib.parse import quote
import os
import uuid
import logging
from datetime import datetime
from app.db.database import get_db
from app.db.models import Admin, Document
from .auth import get_current_admin
from app.config.config import (
    is_sqlite_scheme,
    is_mysql_scheme,
    get_document_dir,
    get_chroma_dir
)
from app.storage import get_storage
from app.rag.vector_factory import get_vector_db

logger = logging.getLogger(__name__)
router = APIRouter()

DOCUMENT_DIR = get_document_dir()
CHROMA_DIR = get_chroma_dir()


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_files: int
    file_types: Dict[str, int]
    total_size: int
    indexed_count: int
    vector_db_type: str = "chromadb"


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

        vector_db_type = "milvus" if is_mysql_scheme() else "chromadb"

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
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """上传文档到知识库（仅上传文件，不自动索引）"""
    try:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
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
            created_at=datetime.utcnow()
        )
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
    request: Optional[IndexRequest] = None,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """将已上传的文档加载到向量数据库（索引化）"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档记录不存在")

        if document.status == "indexed":
            return {"message": "文档已索引，无需重复操作", "document_id": document_id}

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

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
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
            vector_db.add_documents(texts, embeddings)

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
