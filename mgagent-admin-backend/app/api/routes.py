from fastapi import APIRouter, HTTPException, Depends, Header, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import sqlite3
import uuid
import jwt
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path
from app.config.settings import settings, DATA_DIR, DOCUMENT_DIR, CHROMA_DIR
from langchain_chroma import Chroma

router = APIRouter()

SECRET_KEY = "mgagent_admin_secret_key_2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

ADMIN_DB_PATH = Path(__file__).parent.parent.parent / "admin.db"

def init_admin_db():
    conn = sqlite3.connect(str(ADMIN_DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            admin_id TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (admin_id) REFERENCES admins (id)
        )
    ''')
    conn.commit()
    conn.close()

init_admin_db()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="未授权访问")
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="无效的令牌")
        
        conn = sqlite3.connect(str(ADMIN_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE id = ?", (admin_id,))
        admin = cursor.fetchone()
        conn.close()
        
        if not admin:
            raise HTTPException(status_code=401, detail="管理员不存在")
        
        return {
            "id": admin[0],
            "username": admin[1],
            "email": admin[2]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminRegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin: Dict[str, str]

class AdminResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str

@router.post("/auth/login", response_model=TokenResponse)
async def admin_login(request: AdminLoginRequest):
    conn = sqlite3.connect(str(ADMIN_DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (request.username,))
    admin = cursor.fetchone()
    conn.close()
    
    if not admin:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    hashed_password = admin[3]
    if not bcrypt.checkpw(request.password.encode('utf-8'), hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin[0]}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        admin={
            "id": admin[0],
            "username": admin[1],
            "email": admin[2]
        }
    )

@router.post("/auth/register")
async def admin_register(request: AdminRegisterRequest):
    conn = sqlite3.connect(str(ADMIN_DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM admins WHERE username = ?", (request.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    cursor.execute("SELECT * FROM admins WHERE email = ?", (request.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    admin_id = str(uuid.uuid4())
    hashed_password = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    created_at = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO admins (id, username, email, hashed_password, created_at) VALUES (?, ?, ?, ?, ?)",
        (admin_id, request.username, request.email, hashed_password, created_at)
    )
    conn.commit()
    conn.close()
    
    return {
        "message": "管理员注册成功",
        "admin": {
            "id": admin_id,
            "username": request.username,
            "email": request.email,
            "created_at": created_at
        }
    }

@router.get("/auth/me")
async def get_current_admin_info(admin = Depends(get_current_admin)):
    return admin

@router.post("/auth/logout")
async def admin_logout(admin = Depends(get_current_admin)):
    return {"message": "登出成功"}

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

class VectorDBStats(BaseModel):
    total_chunks: int
    persist_directory: str
    embedding_model: str

class VectorChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]

class StorageDBStats(BaseModel):
    database_path: str
    tables: List[str]
    total_records: Dict[str, int]

class ColumnInfo(BaseModel):
    name: str
    type: str
    is_pk: bool

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    record_count: int

class ModelConfig(BaseModel):
    api_key: str
    api_base: str
    model: str

class SystemStatus(BaseModel):
    status: str
    version: str
    uptime: str

class ModelInfo(BaseModel):
    name: str
    api_base: str
    api_key_masked: str
    supported: bool = True

class UpdateUserStatusRequest(BaseModel):
    status: str

class UpdateUserRoleRequest(BaseModel):
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    status: str
    chat_count: int
    max_chats: int
    created_at: str

@router.get("/knowledge-base/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(admin = Depends(get_current_admin)):
    try:
        files = list(DOCUMENT_DIR.glob("*")) if DOCUMENT_DIR.exists() else []
        
        file_types = {}
        total_size = 0
        for file in files:
            if file.is_file():
                ext = file.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
                total_size += file.stat().st_size
        
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
async def list_documents(admin = Depends(get_current_admin)):
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
async def delete_document(filename: str, admin = Depends(get_current_admin)):
    try:
        file_path = DOCUMENT_DIR / filename
        if file_path.exists() and file_path.is_file():
            os.remove(file_path)
            
            chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
            chroma_client._collection.delete(where={"source": str(file_path)})
            
            return {"message": f"文档 {filename} 已删除"}
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/documents/{filename}/download")
async def download_document(filename: str, admin = Depends(get_current_admin)):
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
async def preview_document(filename: str, admin = Depends(get_current_admin)):
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
async def clear_knowledge_base(admin = Depends(get_current_admin)):
    try:
        files = list(DOCUMENT_DIR.glob("*")) if DOCUMENT_DIR.exists() else []
        for file in files:
            if file.is_file():
                os.remove(file)
        
        if CHROMA_DIR.exists():
            chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
            try:
                chroma_client._collection.delete(where={})
            except Exception:
                pass
        
        return {"message": "知识库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/upload")
async def upload_knowledge_base_document(file: UploadFile = File(...), admin = Depends(get_current_admin)):
    try:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")
        
        file_path = DOCUMENT_DIR / file.filename
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
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
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        vectorizer.fit([t.page_content for t in texts])
        
        chroma_client.add_texts(
            [t.page_content for t in texts],
            metadatas=[{"source": str(file_path), "chunk": i} for i in range(len(texts))]
        )
        
        return {
            "message": f"文档 {file.filename} 上传并索引成功",
            "filename": file.filename,
            "file_type": file_ext,
            "file_size": os.path.getsize(file_path),
            "chunks_count": len(texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-db/stats", response_model=VectorDBStats)
async def get_vector_db_stats(admin = Depends(get_current_admin)):
    try:
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
async def list_vector_chunks(limit: int = 10, offset: int = 0, admin = Depends(get_current_admin)):
    try:
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
async def search_vector_db(query: str, k: int = 3, admin = Depends(get_current_admin)):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        results = chroma_client._collection.get(include=["documents", "metadatas"])
        
        documents = results["documents"]
        metadatas = results["metadatas"]
        ids = results["ids"]
        
        if not documents:
            return {"results": [], "message": "向量库为空"}
        
        vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
        vectorizer.fit(documents)
        
        query_vec = vectorizer.transform([query]).toarray()[0]
        doc_vecs = vectorizer.transform(documents).toarray()
        
        similarities = np.dot(doc_vecs, query_vec) / (
            np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
        )
        
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            results.append({
                "id": ids[idx],
                "content": documents[idx],
                "metadata": metadatas[idx],
                "similarity": float(similarities[idx])
            })
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/vector-db/chunks/{chunk_id}")
async def delete_vector_chunk(chunk_id: str, admin = Depends(get_current_admin)):
    try:
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        chroma_client._collection.delete(ids=[chunk_id])
        
        return {"message": f"向量块 {chunk_id} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vector-db/clear")
async def clear_vector_db(admin = Depends(get_current_admin)):
    try:
        chroma_client = Chroma(persist_directory=str(CHROMA_DIR))
        chroma_client._collection.delete(where={})
        
        return {"message": "向量数据库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/stats", response_model=StorageDBStats)
async def get_storage_db_stats(admin = Depends(get_current_admin)):
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        total_records = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_records[table] = cursor.fetchone()[0]
        
        conn.close()
        
        return StorageDBStats(
            database_path=db_path,
            tables=tables,
            total_records=total_records
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/tables", response_model=List[TableInfo])
async def list_tables(admin = Depends(get_current_admin)):
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info_list = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            record_count = cursor.fetchone()[0]
            
            column_list = []
            for col in columns:
                column_list.append({
                    "name": col[1],
                    "type": col[2],
                    "is_pk": bool(col[5])
                })
            
            table_info_list.append(TableInfo(
                name=table,
                columns=column_list,
                record_count=record_count
            ))
        
        conn.close()
        
        return table_info_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/tables/{table_name}/data")
async def get_table_data(table_name: str, limit: int = 50, offset: int = 0, admin = Depends(get_current_admin)):
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="表不存在")
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {"columns": columns, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QueryRequest(BaseModel):
    query: str

@router.post("/storage-db/query")
async def execute_query(request: QueryRequest, admin = Depends(get_current_admin)):
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(request.query)
        
        if request.query.strip().lower().startswith('select'):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            result = {"columns": columns, "data": data}
        else:
            conn.commit()
            result = {"message": f"执行成功，影响 {cursor.rowcount} 行"}
        
        conn.close()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/config", response_model=ModelConfig)
async def get_model_config(admin = Depends(get_current_admin)):
    try:
        return ModelConfig(
            api_key=settings.OPENAI_API_KEY[:4] + "****" + settings.OPENAI_API_KEY[-4:],
            api_base=settings.OPENAI_API_BASE,
            model=settings.OPENAI_MODEL
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/model/config")
async def update_model_config(config: ModelConfig, admin = Depends(get_current_admin)):
    try:
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, "r") as f:
                content = f.read()
            
            if config.api_key and config.api_key != settings.OPENAI_API_KEY:
                content = content.replace(
                    f"OPENAI_API_KEY={settings.OPENAI_API_KEY}",
                    f"OPENAI_API_KEY={config.api_key}"
                )
            
            if config.api_base:
                content = content.replace(
                    f"OPENAI_API_BASE={settings.OPENAI_API_BASE}",
                    f"OPENAI_API_BASE={config.api_base}"
                )
            
            if config.model:
                content = content.replace(
                    f"OPENAI_MODEL={settings.OPENAI_MODEL}",
                    f"OPENAI_MODEL={config.model}"
                )
            
            with open(env_path, "w") as f:
                f.write(content)
        
        return {"message": "模型配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/test")
async def test_model_connection(admin = Depends(get_current_admin)):
    try:
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            temperature=0.1
        )
        
        response = llm.invoke("Hello, this is a test.")
        
        return {"status": "success", "response": response.content[:50]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@router.get("/model/list", response_model=List[ModelInfo])
async def list_available_models(admin = Depends(get_current_admin)):
    models = [
        ModelInfo(
            name="deepseek-chat",
            api_base="https://api.deepseek.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="deepseek-chat-1.5",
            api_base="https://api.deepseek.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="gpt-4o-mini",
            api_base="https://api.openai.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="gpt-4o",
            api_base="https://api.openai.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="gpt-4-turbo",
            api_base="https://api.openai.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="claude-3-sonnet-20240229",
            api_base="https://api.anthropic.com/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="claude-3-opus-20240229",
            api_base="https://api.anthropic.com/v1",
            api_key_masked="******",
            supported=False
        ),
        ModelInfo(
            name="qwen-2-7b-chat",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_masked="******",
            supported=True
        ),
        ModelInfo(
            name="qwen-2-72b-chat",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_masked="******",
            supported=False
        ),
    ]
    return models

import time as time_module
START_TIME = time_module.time()

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(admin = Depends(get_current_admin)):
    uptime_seconds = time_module.time() - START_TIME
    
    days = int(uptime_seconds // (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    
    if days > 0:
        uptime_str = f"{days}天 {hours}小时 {minutes}分钟"
    elif hours > 0:
        uptime_str = f"{hours}小时 {minutes}分钟 {seconds}秒"
    elif minutes > 0:
        uptime_str = f"{minutes}分钟 {seconds}秒"
    else:
        uptime_str = f"{seconds}秒"
    
    return SystemStatus(
        status="healthy",
        version="1.0.0",
        uptime=uptime_str
    )

@router.get("/system/info")
async def get_system_info(admin = Depends(get_current_admin)):
    import psutil
    import platform
    
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

import httpx

MGAGENT_BACKEND_URL = "http://localhost:8000/api"

@router.get("/dashboard/stats")
async def get_dashboard_stats(admin = Depends(get_current_admin)):
    try:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM chat_messages WHERE role = 'assistant'")
        model_calls = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chat_sessions")
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "model_calls": model_calls,
            "total_sessions": total_sessions,
            "total_users": total_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_users_list(status: Optional[str] = None, admin = Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        params = {}
        if status:
            params["status"] = status
        response = await client.get(f"{MGAGENT_BACKEND_URL}/users", params=params)
        return response.json()

@router.get("/users/{user_id}")
async def get_user_endpoint(user_id: str, admin = Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MGAGENT_BACKEND_URL}/users/{user_id}")
        return response.json()

@router.put("/users/{user_id}/status")
async def update_user_status_endpoint(user_id: str, request: UpdateUserStatusRequest, admin = Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MGAGENT_BACKEND_URL}/users/{user_id}/status", json={"status": request.status})
        return response.json()

@router.put("/users/{user_id}/role")
async def update_user_role_endpoint(user_id: str, request: UpdateUserRoleRequest, admin = Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MGAGENT_BACKEND_URL}/users/{user_id}/role", json={"role": request.role})
        return response.json()

@router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: str, admin = Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{MGAGENT_BACKEND_URL}/users/{user_id}")
        return response.json()