"""
路由层 - 仅接收请求、调用 service、返回响应
"""
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as SQLAlchemySession
from typing import List, Optional

from app.db.database import get_db
from app.db.models import User
from app.api.deps import get_current_user, get_optional_user
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RegisterResponse,
    ChatRequest,
    ChatResponse,
    SessionResponse,
    SessionDetailResponse,
    UpdateSessionRequest,
    DocumentResponse,
    UpdateUserStatusRequest,
    UpdateUserRoleRequest,
)
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService
from app.exceptions import BusinessException
from app.core.logger import logger
from app.agent.core import enterprise_agent, get_llm

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: SQLAlchemySession = Depends(get_db)):
    """用户登录"""
    result = UserService.login(db, request.username, request.password)
    return TokenResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=result["user"],
    )


@router.post("/auth/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, db: SQLAlchemySession = Depends(get_db)):
    """用户注册"""
    user = UserService.register(db, request.username, request.email, request.password)

    # 通知管理员
    try:
        NotificationService.notify_new_user_registration(request.username, request.email)
    except Exception as e:
        logger.warning(f"通知管理员失败: {str(e)}")

    return RegisterResponse(
        message="注册成功，请等待管理员审批",
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "chat_count": user.chat_count,
            "max_chats": user.max_chats,
            "created_at": user.created_at.isoformat(),
        },
    )


@router.get("/auth/me")
async def get_current_user_info(user: Optional[User] = Depends(get_optional_user)):
    """获取当前用户信息"""
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "chat_count": user.chat_count,
        "max_chats": user.max_chats,
        "created_at": user.created_at.isoformat(),
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: SQLAlchemySession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """同步聊天"""
    import asyncio

    result = await asyncio.to_thread(
        ChatService.chat,
        db=db,
        message=request.message,
        session_id=request.session_id,
        user=user,
    )
    return ChatResponse(
        session_id=result["session_id"],
        response=result["response"],
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: SQLAlchemySession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """流式聊天"""
    # 先处理会话和权限检查
    if request.session_id:
        session = ChatService.get_session(db, request.session_id)
        if user and session.user_id != user.id:
            raise BusinessException("无权访问此会话", status_code=403, code="FORBIDDEN")
    else:
        uid = user.id if user else "anonymous"
        session = ChatService.create_session(db, uid)

    # 检查用户状态和次数
    ChatService._check_user_status(user, db)

    # 保存用户消息
    from app.db.crud import add_message
    add_message(db, session.id, "user", request.message)

    # 检查模型配置
    try:
        get_llm()
    except ValueError as e:
        error_msg = str(e)
        if "未配置有效的模型" in error_msg or "未配置活跃的模型" in error_msg:
            error_content = "系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试"
            add_message(db, session.id, "assistant", error_content)
            raise BusinessException(
                error_content,
                status_code=503,
                code="MODEL_NOT_CONFIGURED",
            )
        raise

    async def generate():
        full_response = ""
        history = ChatService._build_history(db, session.id)
        for chunk in enterprise_agent.stream_chat(request.message, history):
            full_response += chunk
            yield chunk

        add_message(db, session.id, "assistant", full_response)
        if user:
            from app.db.crud import increment_chat_count
            increment_chat_count(db, user.id)
        else:
            from app.db.crud import increment_anonymous_chat_count
            increment_anonymous_chat_count(db)

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/chat/with-file", response_model=ChatResponse)
async def chat_with_file(
    message: str = "",
    session_id: Optional[str] = None,
    file: UploadFile = File(None),
    db: SQLAlchemySession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """带文件的聊天"""
    file_tuple = None
    if file:
        file_data = await file.read()
        file_tuple = (file.filename, file_data)

    result = ChatService.chat_with_file(
        db=db,
        message=message,
        session_id=session_id,
        user=user,
        file=file_tuple,
    )
    return ChatResponse(
        session_id=result["session_id"],
        response=result["response"],
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    db: SQLAlchemySession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """获取会话列表"""
    user_id = user.id if user else "anonymous"
    sessions = ChatService.list_sessions(db, user_id)
    return [SessionResponse(**s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """获取单个会话详情"""
    result = ChatService.get_session_messages(db, session_id)
    return SessionDetailResponse(**result)


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    db: SQLAlchemySession = Depends(get_db),
):
    """更新会话标题"""
    session = ChatService.update_session_title(db, session_id, request.title)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() + 'Z',
        updated_at=session.updated_at.isoformat() + 'Z',
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """删除会话"""
    ChatService.delete_session(db, session_id)
    return {"message": "会话已删除"}


@router.post("/documents", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: SQLAlchemySession = Depends(get_db),
):
    """上传文档"""
    file_data = await file.read()
    result = DocumentService.upload_document(db, file.filename, file_data)
    return DocumentResponse(**result)


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    db: SQLAlchemySession = Depends(get_db),
):
    """获取文档列表"""
    documents = DocumentService.list_documents(db)
    return [DocumentResponse(**d) for d in documents]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_endpoint(
    document_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """获取单个文档"""
    result = DocumentService.get_document_by_id(db, document_id)
    return DocumentResponse(**result)


@router.delete("/documents/{document_id}")
async def delete_document_endpoint(
    document_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """删除文档"""
    DocumentService.delete_document(db, document_id)
    return {"message": "文档已删除"}


@router.get("/tools")
async def get_tools():
    """获取工具列表"""
    tools = []
    for name, info in enterprise_agent.tools.items():
        tools.append({
            "name": name,
            "description": info["description"],
        })
    return {"tools": tools}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@router.get("/users")
async def get_users_list(
    db: SQLAlchemySession = Depends(get_db),
    status: Optional[str] = None,
):
    """获取用户列表"""
    users = UserService.list_users(db, status=status)
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "chat_count": u.chat_count,
            "max_chats": u.max_chats,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.get("/users/{user_id}")
async def get_user_endpoint(
    user_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """获取单个用户"""
    user = UserService.get_user_info(db, user_id)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "chat_count": user.chat_count,
        "max_chats": user.max_chats,
        "created_at": user.created_at.isoformat(),
    }


@router.put("/users/{user_id}/status")
async def update_user_status_endpoint(
    user_id: str,
    request: UpdateUserStatusRequest,
    db: SQLAlchemySession = Depends(get_db),
):
    """更新用户状态"""
    user = UserService.update_status(db, user_id, request.status)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "chat_count": user.chat_count,
        "max_chats": user.max_chats,
        "created_at": user.created_at.isoformat(),
    }


@router.put("/users/{user_id}/role")
async def update_user_role_endpoint(
    user_id: str,
    request: UpdateUserRoleRequest,
    db: SQLAlchemySession = Depends(get_db),
):
    """更新用户角色"""
    user = UserService.update_role(db, user_id, request.role)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "chat_count": user.chat_count,
        "max_chats": user.max_chats,
        "created_at": user.created_at.isoformat(),
    }


@router.delete("/users/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    db: SQLAlchemySession = Depends(get_db),
):
    """删除用户"""
    UserService.delete_user(db, user_id)
    return {"message": "用户已删除"}