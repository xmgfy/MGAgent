from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional
import uuid
import os
import jwt
from datetime import datetime, timedelta
from app.db.crud import (
    create_chat_session, get_chat_session, get_chat_sessions,
    update_chat_session_title, delete_chat_session, add_message, get_messages,
    create_document, get_document, get_documents, update_document_status, delete_document,
    create_user, get_user, get_user_by_username, get_user_by_email, get_users,
    update_user_status, update_user_role, increment_chat_count, verify_password,
    get_anonymous_chat_count, increment_anonymous_chat_count
)
from app.db.models import Base
from sqlalchemy import create_engine
from app.config.settings import settings
engine = create_engine(settings.DATABASE_URL)
from app.agent.core import enterprise_agent
from app.rag.loader import DocumentLoader
from app.rag.retriever import vector_retriever
from app.config.settings import DOCUMENT_DIR

router = APIRouter()

SECRET_KEY = settings.OPENAI_API_KEY[:32]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    db = SQLAlchemySession(bind=engine)
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(authorization: str = Header(None), db: SQLAlchemySession = Depends(get_db)):
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return get_user(db, user_id)
        return None
    except Exception:
        return None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str

class Message(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

class Session(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class UpdateSessionRequest(BaseModel):
    title: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    status: str
    chat_count: int
    max_chats: int
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UpdateUserStatusRequest(BaseModel):
    status: str

class UpdateUserRoleRequest(BaseModel):
    role: str

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: SQLAlchemySession = Depends(get_db)):
    user = verify_password(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="账号尚未通过审批，请联系管理员")
    elif user.status == "frozen":
        raise HTTPException(status_code=403, detail="账号已被冻结，请联系管理员")
    elif user.status == "disabled":
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")
    elif user.status == "rejected":
        raise HTTPException(status_code=403, detail="账号已被拒绝，请联系管理员")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            chat_count=user.chat_count,
            max_chats=user.max_chats,
            created_at=user.created_at.isoformat()
        )
    )

@router.post("/auth/register")
async def register(request: RegisterRequest, db: SQLAlchemySession = Depends(get_db)):
    if get_user_by_username(db, request.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    if get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    user = create_user(db, request.username, request.email, request.password)
    
    try:
        import requests
        requests.post(
            f"{settings.ADMIN_API_URL}/notifications/external",
            params={
                "type": "user_registration",
                "title": "新用户注册申请",
                "message": f"用户 {user.username} ({user.email}) 提交了注册申请，请进行审批"
            },
            timeout=5
        )
    except Exception:
        pass
    
    return {
        "message": "注册成功，请等待管理员审批",
        "user": UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            chat_count=user.chat_count,
            max_chats=user.max_chats,
            created_at=user.created_at.isoformat()
        )
    }

@router.get("/auth/me", response_model=Optional[UserResponse])
async def get_current_user_info(user = Depends(get_current_user)):
    if not user:
        return None
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        chat_count=user.chat_count,
        max_chats=user.max_chats,
        created_at=user.created_at.isoformat()
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: SQLAlchemySession = Depends(get_db), user = Depends(get_current_user)):
    user_id = user.id if user else None
    
    if request.session_id:
        session = get_chat_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        if user and session.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
    else:
        if user:
            session = create_chat_session(db, user.id)
        else:
            session = create_chat_session(db, "anonymous")
    
    if user:
        if user.status == "pending":
            raise HTTPException(status_code=403, detail="账号尚未通过审批，请联系管理员")
        if user.chat_count >= user.max_chats:
            raise HTTPException(status_code=403, detail=f"已达到最大问答次数限制（{user.max_chats}次），请联系管理员开通更多次数")
    else:
        anonymous_count = get_anonymous_chat_count(db)
        if anonymous_count >= 3:
            raise HTTPException(status_code=403, detail="已达到免费问答次数限制（3次），请登录账号继续使用")
    
    add_message(db, session.id, "user", request.message)
    
    history = []
    messages = get_messages(db, session.id)
    for msg in messages[:-1]:
        history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, enterprise_agent.chat, request.message, history),
            timeout=30.0
        )
        add_message(db, session.id, "assistant", response)
        
        if user:
            increment_chat_count(db, user.id)
        else:
            increment_anonymous_chat_count(db)
        
        return ChatResponse(session_id=session.id, response=response)
    except ValueError as e:
        if "未配置有效的模型" in str(e):
            error_msg = "系统服务暂时不可用，请稍后再试"
            add_message(db, session.id, "assistant", error_msg)
            raise HTTPException(status_code=503, detail={"message": error_msg, "session_id": session.id})
        raise
    except asyncio.TimeoutError:
        add_message(db, session.id, "assistant", "请求超时，请稍后重试")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except Exception as e:
        error_msg = f"处理请求时发生错误: {str(e)}"
        add_message(db, session.id, "assistant", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: SQLAlchemySession = Depends(get_db), user = Depends(get_current_user)):
    user_id = user.id if user else None
    
    if request.session_id:
        session = get_chat_session(db, request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        if user and session.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
    else:
        if user:
            session = create_chat_session(db, user.id)
        else:
            session = create_chat_session(db, "anonymous")
    
    if user:
        if user.status == "pending":
            raise HTTPException(status_code=403, detail="账号尚未通过审批，请联系管理员")
        if user.chat_count >= user.max_chats:
            raise HTTPException(status_code=403, detail=f"已达到最大问答次数限制（{user.max_chats}次），请联系管理员开通更多次数")
    else:
        anonymous_count = get_anonymous_chat_count(db)
        if anonymous_count >= 3:
            raise HTTPException(status_code=403, detail="已达到免费问答次数限制（3次），请登录账号继续使用")
    
    add_message(db, session.id, "user", request.message)
    
    history = []
    messages = get_messages(db, session.id)
    for msg in messages[:-1]:
        history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    try:
        from app.agent.core import get_llm
        get_llm()
    except ValueError as e:
        if "未配置有效的模型" in str(e):
            error_msg = "系统服务暂时不可用，请稍后再试"
            add_message(db, session.id, "assistant", error_msg)
            raise HTTPException(status_code=503, detail={"message": error_msg, "session_id": session.id})
        raise
    
    async def generate():
        full_response = ""
        for chunk in enterprise_agent.stream_chat(request.message, history):
            full_response += chunk
            yield chunk
        
        add_message(db, session.id, "assistant", full_response)
        if user:
            increment_chat_count(db, user.id)
        else:
            increment_anonymous_chat_count(db)
    
    return StreamingResponse(generate(), media_type="text/plain")

@router.post("/chat/with-file")
async def chat_with_file(
    message: str = "",
    session_id: Optional[str] = None,
    file: UploadFile = File(None),
    db: SQLAlchemySession = Depends(get_db),
    user = Depends(get_current_user)
):
    user_id = user.id if user else None
    
    if session_id:
        session = get_chat_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        if user and session.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
    else:
        if user:
            session = create_chat_session(db, user.id)
        else:
            session = create_chat_session(db, "anonymous")
    
    if user:
        if user.status == "pending":
            raise HTTPException(status_code=403, detail="账号尚未通过审批，请联系管理员")
        if user.chat_count >= user.max_chats:
            raise HTTPException(status_code=403, detail=f"已达到最大问答次数限制（{user.max_chats}次），请联系管理员开通更多次数")
    else:
        anonymous_count = get_anonymous_chat_count(db)
        if anonymous_count >= 3:
            raise HTTPException(status_code=403, detail="已达到免费问答次数限制（3次），请登录账号继续使用")
    
    file_content = ""
    if file:
        allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")
        
        try:
            loader = DocumentLoader()
            file_data = await file.read()
            temp_file_path = os.path.join(DOCUMENT_DIR, f"temp_{uuid.uuid4()}{file_ext}")
            with open(temp_file_path, "wb") as f:
                f.write(file_data)
            
            docs = loader.load_file(temp_file_path)
            file_content = "\n\n".join([doc.page_content for doc in docs])
            
            os.remove(temp_file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
    
    full_message = message
    if file_content:
        full_message = f"参考以下文件内容回答问题：\n\n文件内容：\n{file_content}\n\n问题：{message}"
    
    add_message(db, session.id, "user", full_message)
    
    history = []
    messages = get_messages(db, session.id)
    for msg in messages[:-1]:
        history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, enterprise_agent.chat, full_message, history),
            timeout=30.0
        )
        add_message(db, session.id, "assistant", response)
        
        if user:
            increment_chat_count(db, user.id)
        else:
            increment_anonymous_chat_count(db)
        
        return ChatResponse(session_id=session.id, response=response)
    except ValueError as e:
        if "未配置有效的模型" in str(e):
            error_msg = "系统服务暂时不可用，请稍后再试"
            add_message(db, session.id, "assistant", error_msg)
            raise HTTPException(status_code=503, detail={"message": error_msg, "session_id": session.id})
        raise
    except asyncio.TimeoutError:
        add_message(db, session.id, "assistant", "请求超时，请稍后重试")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except Exception as e:
        error_msg = f"处理请求时发生错误: {str(e)}"
        add_message(db, session.id, "assistant", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/sessions", response_model=List[Session])
async def get_sessions(db: SQLAlchemySession = Depends(get_db), user = Depends(get_current_user)):
    user_id = user.id if user else "anonymous"
    sessions = get_chat_sessions(db, user_id)
    return [Session(
        id=s.id,
        title=s.title,
        created_at=s.created_at.isoformat() + 'Z',
        updated_at=s.updated_at.isoformat() + 'Z'
    ) for s in sessions]

@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: SQLAlchemySession = Depends(get_db)):
    session = get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = get_messages(db, session_id)
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat() + 'Z',
        "updated_at": session.updated_at.isoformat() + 'Z',
        "messages": [Message(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat() + 'Z'
        ) for m in messages]
    }

@router.put("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest, db: SQLAlchemySession = Depends(get_db)):
    session = update_chat_session_title(db, session_id, request.title)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return Session(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() + 'Z',
        updated_at=session.updated_at.isoformat() + 'Z'
    )

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: SQLAlchemySession = Depends(get_db)):
    success = delete_chat_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}

@router.post("/documents")
async def upload_document(file: UploadFile = File(...), db: SQLAlchemySession = Depends(get_db)):
    allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(DOCUMENT_DIR, f"{file_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    document = create_document(db, file.filename, file_ext, os.path.getsize(file_path))
    
    try:
        loader = DocumentLoader()
        docs = loader.load_file(file_path)
        vector_retriever.add_documents(docs)
        update_document_status(db, document.id, "indexed")
    except Exception as e:
        update_document_status(db, document.id, "error")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")
    
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        created_at=document.created_at.isoformat()
    )

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: SQLAlchemySession = Depends(get_db)):
    documents = get_documents(db)
    return [DocumentResponse(
        id=d.id,
        filename=d.filename,
        file_type=d.file_type,
        file_size=d.file_size,
        status=d.status,
        created_at=d.created_at.isoformat()
    ) for d in documents]

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(document_id: str, db: SQLAlchemySession = Depends(get_db)):
    document = get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        created_at=document.created_at.isoformat()
    )

@router.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: str, db: SQLAlchemySession = Depends(get_db)):
    success = delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "文档已删除"}

@router.get("/tools")
async def get_tools():
    tools = []
    for name, info in enterprise_agent.tools.items():
        tools.append({
            "name": name,
            "description": info["description"]
        })
    return {"tools": tools}

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/users", response_model=List[UserResponse])
async def get_users_list(db: SQLAlchemySession = Depends(get_db), status: Optional[str] = None):
    users = get_users(db, status=status)
    return [UserResponse(
        id=u.id,
        username=u.username,
        email=u.email,
        role=u.role,
        status=u.status,
        chat_count=u.chat_count,
        max_chats=u.max_chats,
        created_at=u.created_at.isoformat()
    ) for u in users]

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(user_id: str, db: SQLAlchemySession = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        chat_count=user.chat_count,
        max_chats=user.max_chats,
        created_at=user.created_at.isoformat()
    )

@router.put("/users/{user_id}/status")
async def update_user_status_endpoint(user_id: str, request: UpdateUserStatusRequest, db: SQLAlchemySession = Depends(get_db)):
    user = update_user_status(db, user_id, request.status)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        chat_count=user.chat_count,
        max_chats=user.max_chats,
        created_at=user.created_at.isoformat()
    )

@router.put("/users/{user_id}/role")
async def update_user_role_endpoint(user_id: str, request: UpdateUserRoleRequest, db: SQLAlchemySession = Depends(get_db)):
    user = update_user_role(db, user_id, request.role)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        chat_count=user.chat_count,
        max_chats=user.max_chats,
        created_at=user.created_at.isoformat()
    )

@router.delete("/users/{user_id}")
async def delete_user_endpoint(user_id: str, db: SQLAlchemySession = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "用户已删除"}