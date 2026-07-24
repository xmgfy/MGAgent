from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict
import os
import uuid
from pathlib import Path
from datetime import datetime
from app.db.database import get_db
from app.db.models import Admin, Document
from .auth import get_current_admin
from app.config.settings import DOCUMENT_DIR, CHROMA_DIR

router = APIRouter()

class KnowledgeBaseStats(BaseModel):
    total_documents: int
    total_files: int
    file_types: Dict[str, int]
    total_size: int
    indexed_count: int

class DocumentInfo(BaseModel):
    filename: str
    file_type: str
    file_size: int
    created_at: str
    status: str = "indexed"

@router.get("/knowledge-base/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(admin: Admin = Depends(get_current_admin)):
    try:
        files = list(DOCUMENT_DIR.glob("*")) if DOCUMENT_DIR.exists() else []
        
        file_types = {}
        total_size = 0
        for file in files:
            if file.is_file():
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
                total_size += file.stat().st_size
        
        from langchain_chroma import Chroma
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        total_chunks = chroma_client._collection.count()
        
        return KnowledgeBaseStats(
            total_documents=total_chunks,
            total_files=len(files),
            file_types=file_types,
            total_size=total_size,
            indexed_count=total_chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/documents", response_model=List[DocumentInfo])
async def list_documents(admin: Admin = Depends(get_current_admin)):
    try:
        files = list(DOCUMENT_DIR.glob("*")) if DOCUMENT_DIR.exists() else []
        documents = []
        
        for file in files:
            if file.is_file():
                documents.append(DocumentInfo(
                    filename=file.name,
                    file_type=file.suffix.lower(),
                    file_size=file.stat().st_size,
                    created_at=str(file.stat().st_mtime),
                    status="indexed"
                ))
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-base/documents/{filename}")
async def delete_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        file_path = DOCUMENT_DIR / filename
        if file_path.exists() and file_path.is_file():
            os.remove(file_path)
            
            from langchain_chroma import Chroma
            chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
            chroma_client._collection.delete(where={"source": str(file_path)})
            
            return {"message": f"文档 {filename} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/documents/{filename}/download")
async def download_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        file_path = DOCUMENT_DIR / filename
        if file_path.exists() and file_path.is_file():
            from fastapi.responses import FileResponse
            return FileResponse(
                path=str(file_path),
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/documents/{filename}/preview")
async def preview_document(filename: str, admin: Admin = Depends(get_current_admin)):
    try:
        file_path = DOCUMENT_DIR / filename
        if file_path.exists() and file_path.is_file():
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == ".txt" or file_ext == ".md":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"content": content, "type": "text"}
            
            elif file_ext == ".pdf":
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(str(file_path))
                    content = ""
                    for page in reader.pages:
                        content += page.extract_text()
                    return {"content": content[:5000], "type": "text", "truncated": len(content) > 5000}
                except ImportError:
                    return {"content": "需要安装 PyPDF2 才能预览 PDF 文件", "type": "error"}
            
            elif file_ext == ".docx":
                try:
                    import docx2txt
                    content = docx2txt.process(str(file_path))
                    return {"content": content[:5000], "type": "text", "truncated": len(content) > 5000}
                except ImportError:
                    return {"content": "需要安装 docx2txt 才能预览 DOCX 文件", "type": "error"}
            
            else:
                return {"content": f"不支持预览 {file_ext} 格式的文件", "type": "error"}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/clear")
async def clear_knowledge_base(admin: Admin = Depends(get_current_admin)):
    try:
        files = list(DOCUMENT_DIR.glob("*")) if DOCUMENT_DIR.exists() else []
        for file in files:
            if file.is_file():
                os.remove(file)
        
        if CHROMA_DIR.exists():
            from langchain_chroma import Chroma
            chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
            try:
                chroma_client._collection.delete(where={})
            except Exception:
                pass
        
        return {"message": "知识库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/upload")
async def upload_knowledge_base_document(file: UploadFile = File(...), admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")
        
        file_path = DOCUMENT_DIR / file.filename
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        file_size = os.path.getsize(file_path)
        
        from langchain_chroma import Chroma
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        
        from langchain_community.document_loaders import PyPDFLoader, TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        import docx2txt
        
        docs = []
        if file_ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
        elif file_ext == ".docx":
            text = docx2txt.process(str(file_path))
            docs = [{"page_content": text, "metadata": {"source": str(file_path)}}]
        elif file_ext == ".md":
            loader = TextLoader(str(file_path))
            docs = loader.load()
        else:
            loader = TextLoader(str(file_path))
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
        
        chroma_client.add_texts(
            [t.page_content for t in texts],
            metadatas=[{"source": str(file_path), "chunk": i} for i in range(len(texts))]
        )
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
