from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
import os
import uuid
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


@router.get("/knowledge-base/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        files = storage.list_files()
        
        file_types = {}
        total_size = 0
        for file in files:
            ext = os.path.splitext(file["name"])[1].lower()
            file_types[ext] = file_types.get(ext, 0) + 1
            total_size += file["size"]
        
        try:
            vector_db = get_vector_db()
            total_chunks = vector_db.get_total_count()
        except Exception:
            total_chunks = 0
            
        vector_db_type = "milvus" if is_mysql_scheme() else "chromadb"
        
        return KnowledgeBaseStats(
            total_documents=total_chunks,
            total_files=len(files),
            file_types=file_types,
            total_size=total_size,
            indexed_count=total_chunks,
            vector_db_type=vector_db_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents", response_model=List[DocumentInfo])
async def list_documents(admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        files = storage.list_files()
        documents = []
        
        for file in files:
            documents.append(DocumentInfo(
                filename=file["name"],
                file_type=os.path.splitext(file["name"])[1].lower(),
                file_size=file["size"],
                created_at=str(file.get("created_at", "")),
                status="indexed"
            ))
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge-base/documents/{filename}")
async def delete_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        
        # 查找文件
        file_info = storage.get_file_info(filename)
        if not file_info:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除文件
        storage.delete(filename)
        
        # 删除向量数据库中的相关数据
        try:
            vector_db = get_vector_db()
            chunks = vector_db.get_all_chunks()
            ids_to_delete = [
                chunk["id"] for chunk in chunks 
                if chunk.get("metadata", {}).get("source") == filename
            ]
            if ids_to_delete:
                vector_db.delete_by_ids(ids_to_delete)
        except Exception:
            pass
        
        return {"message": f"文档 {filename} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents/{filename}/download")
async def download_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        
        if not storage.exists(filename):
            raise HTTPException(status_code=404, detail="文档不存在")
        
        file_data = storage.download(filename)
        
        return Response(
            content=file_data,
            media_type='application/octet-stream',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/documents/{filename}/preview")
async def preview_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        
        if not storage.exists(filename):
            raise HTTPException(status_code=404, detail="文档不存在")
        
        file_data = storage.download(filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # 写入临时文件用于预览
        temp_dir = get_document_dir()
        temp_file_path = temp_dir / f"preview_{uuid.uuid4()}{file_ext}"
        with open(temp_file_path, "wb") as f:
            f.write(file_data)
        
        try:
            if file_ext == ".txt" or file_ext == ".md":
                with open(temp_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content, "type": "text"}
            
            elif file_ext == ".pdf":
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(str(temp_file_path))
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                    return {"content": content[:5000], "type": "text", "truncated": len(content) > 5000}
                except ImportError:
                    return {"content": "需要安装 PyPDF2 才能预览 PDF 文件", "type": "error"}
            
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
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/clear")
async def clear_knowledge_base(admin: Admin = Depends(get_current_admin)):
    try:
        storage = get_storage()
        files = storage.list_files()
        for file in files:
            storage.delete(file["name"])
        
        vector_db = get_vector_db()
        vector_db.clear_all()
        
        return {"message": "知识库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/upload")
async def upload_knowledge_base_document(
    file: UploadFile = File(...), 
    admin: Admin = Depends(get_current_admin), 
    db: Session = Depends(get_db)
):
    try:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")
        
        file_data = await file.read()
        file_size = len(file_data)
        
        # 上传到存储
        storage = get_storage()
        stored_path = storage.upload(file.filename, file_data)
        
        # 下载文件用于处理（如果是 MinIO 存储）
        temp_dir = get_document_dir()
        temp_file_path = temp_dir / f"process_{uuid.uuid4()}{file_ext}"
        
        try:
            # 从存储下载文件
            if storage.exists(stored_path):
                content = storage.download(stored_path)
                with open(temp_file_path, "wb") as f:
                    f.write(content)
            else:
                # 本地存储场景，直接使用路径
                temp_file_path = stored_path
            
            from langchain_community.document_loaders import PyPDFLoader, TextLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            import docx2txt
            
            docs = []
            if file_ext == ".pdf":
                loader = PyPDFLoader(str(temp_file_path))
                docs = loader.load()
            elif file_ext == ".docx":
                text = docx2txt.process(str(temp_file_path))
                docs = [{"page_content": text, "metadata": {"source": stored_path}}]
            elif file_ext == ".md":
                loader = TextLoader(str(temp_file_path))
                docs = loader.load()
            else:
                loader = TextLoader(str(temp_file_path))
                docs = loader.load()
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len
            )
            
            if isinstance(docs[0], dict):
                texts = splitter.create_documents([docs[0]["page_content"]])
            else:
                texts = splitter.split_documents(docs)
            
            # 获取向量数据库实例并添加文档
            vector_db = get_vector_db()
            embeddings = [[0.0] * 1536 for _ in texts]  # 占位符，实际应由 embedding 服务生成
            
            vector_db.add_documents(texts, embeddings)
            
            document = Document(
                id=str(uuid.uuid4()),
                filename=file.filename,
                file_type=file_ext,
                file_size=file_size,
                status="indexed",
                tenant_id=admin.tenant_id,
                created_at=datetime.utcnow()
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            
            return {
                "message": f"文档 {file.filename} 上传并索引成功",
                "filename": file.filename,
                "file_type": file_ext,
                "file_size": file_size,
                "chunks_count": len(texts)
            }
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path) and temp_file_path != stored_path:
                os.remove(temp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
