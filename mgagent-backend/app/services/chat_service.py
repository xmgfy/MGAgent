"""
聊天服务层
"""
import asyncio
import os
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.db.crud import (
    create_chat_session,
    get_chat_session,
    get_chat_sessions,
    update_chat_session_title,
    delete_chat_session,
    add_message,
    get_messages,
    get_anonymous_chat_count,
    increment_anonymous_chat_count,
)
from app.db.models import User, ChatSession, ChatMessage
from app.core.logger import logger
from app.exceptions import (
    BusinessException,
    NotFoundException,
    ValidationException,
    ForbiddenException,
    ModelNotConfiguredException,
    TimeoutException,
    ChatLimitExceededException,
)
from app.agent.core import enterprise_agent, get_llm
from app.storage import get_storage
from app.rag.loader import DocumentLoader

ANONYMOUS_USER_ID = "anonymous"
ANONYMOUS_MAX_CHATS = 3
DEFAULT_TIMEOUT = 30.0


class ChatService:
    """聊天服务"""

    @staticmethod
    def create_session(db: Session, user_id: Optional[str] = None) -> ChatSession:
        """创建会话"""
        uid = user_id or ANONYMOUS_USER_ID
        session = create_chat_session(db, uid)
        logger.info(f"创建会话: {session.id}, 用户: {uid}")
        return session

    @staticmethod
    def get_session(db: Session, session_id: str) -> ChatSession:
        """获取会话"""
        session = get_chat_session(db, session_id)
        if not session:
            raise NotFoundException("会话不存在")
        return session

    @staticmethod
    def get_user_sessions(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ChatSession]:
        """获取用户会话列表"""
        return get_chat_sessions(db, user_id, skip=skip, limit=limit)

    @staticmethod
    def update_session_title(
        db: Session,
        session_id: str,
        title: str,
    ) -> ChatSession:
        """更新会话标题"""
        session = update_chat_session_title(db, session_id, title)
        if not session:
            raise NotFoundException("会话不存在")
        return session

    @staticmethod
    def delete_session(db: Session, session_id: str) -> None:
        """删除会话"""
        if not delete_chat_session(db, session_id):
            raise NotFoundException("会话不存在")
        logger.info(f"删除会话: {session_id}")

    @staticmethod
    def _check_user_access(user: Optional[User], session: ChatSession) -> None:
        """检查用户访问权限"""
        if user and session.user_id != user.id:
            raise ForbiddenException("无权访问此会话")

    @staticmethod
    def _check_user_status(user: Optional[User], db: Session) -> None:
        """检查用户状态和次数限制"""
        if not user:
            anonymous_count = get_anonymous_chat_count(db)
            if anonymous_count >= ANONYMOUS_MAX_CHATS:
                raise ChatLimitExceededException(
                    f"已达到免费问答次数限制（{ANONYMOUS_MAX_CHATS}次），请登录账号继续使用"
                )
        else:
            if user.status == "pending":
                raise ForbiddenException("账号尚未通过审批，请联系管理员")
            # 已登录用户不限问答次数，仅检查账号状态

    @staticmethod
    def _build_history(db: Session, session_id: str) -> list[dict]:
        """构建聊天历史"""
        history = []
        messages = get_messages(db, session_id)
        for msg in messages[:-1]:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        return history

    @staticmethod
    def chat(
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
    ) -> dict:
        """同步聊天"""
        user_id = user.id if user else ANONYMOUS_USER_ID

        # 获取或创建会话
        if session_id:
            session = ChatService.get_session(db, session_id)
            ChatService._check_user_access(user, session)
        else:
            session = ChatService.create_session(db, user_id)

        # 检查用户状态和次数
        ChatService._check_user_status(user, db)

        # 保存用户消息
        add_message(db, session.id, "user", message)

        # 构建历史
        history = ChatService._build_history(db, session.id)

        # 调用 Agent（同步调用，在路由层已转为异步）
        try:
            response_result = enterprise_agent.chat(message, history)
        except ValueError as e:
            error_msg = str(e)
            if "未配置有效的模型" in error_msg or "未配置活跃的模型" in error_msg:
                error_content = "系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试"
                add_message(db, session.id, "assistant", error_content)
                raise ModelNotConfiguredException()
            raise
        except Exception as e:
            logger.error(f"聊天处理异常: {str(e)}")
            add_message(db, session.id, "assistant", f"处理请求时发生错误: {str(e)}")
            raise

        # 保存助手回复
        add_message(db, session.id, "assistant", response_result)

        # 更新聊天次数
        if user:
            from app.db.crud import increment_chat_count
            increment_chat_count(db, user.id)
        else:
            increment_anonymous_chat_count(db)

        return {
            "session_id": session.id,
            "response": response_result,
        }

    @staticmethod
    def chat_with_file(
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        user: Optional[User] = None,
        file: Optional[tuple] = None,
    ) -> dict:
        """带文件的聊天"""
        user_id = user.id if user else ANONYMOUS_USER_ID

        # 获取或创建会话
        if session_id:
            session = ChatService.get_session(db, session_id)
            ChatService._check_user_access(user, session)
        else:
            session = ChatService.create_session(db, user_id)

        # 检查用户状态和次数
        ChatService._check_user_status(user, db)

        # 处理文件
        file_content = ""
        if file:
            filename, file_data = file
            allowed_extensions = [".pdf", ".txt", ".docx", ".md"]
            file_ext = filename[filename.rfind('.'):] if '.' in filename else ''

            if file_ext not in allowed_extensions:
                raise ValidationException(
                    f"不支持的文件格式，支持的格式: {', '.join(allowed_extensions)}"
                )

            try:
                storage = get_storage()
                loader = DocumentLoader()
                
                # 上传到存储并获取临时路径
                stored_path = storage.upload(filename, file_data)
                
                # 如果是 MinIO 存储，需要下载到本地临时文件
                if hasattr(storage, 'download') and not os.path.exists(stored_path):
                    # MinIO 存储场景：下载到本地临时文件
                    temp_file_path = f"{os.getcwd()}/data/documents/{uuid.uuid4()}{file_ext}"
                    file_content = storage.download(stored_path)
                    with open(temp_file_path, "wb") as f:
                        f.write(file_content)
                    docs = loader.load_file(temp_file_path)
                    file_content_text = "\n\n".join([doc.page_content for doc in docs])
                    # 清理临时文件
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                else:
                    # 本地存储场景：直接使用路径
                    docs = loader.load_file(stored_path)
                    file_content_text = "\n\n".join([doc.page_content for doc in docs])
                    # 清理存储的临时文件
                    storage.delete(stored_path)
                
                file_content = file_content_text
            except OSError as e:
                logger.error(f"文件处理失败: {str(e)}")
                raise BusinessException(f"文件处理失败: {str(e)}")

        # 构建完整消息
        full_message = message
        if file_content:
            full_message = f"参考以下文件内容回答问题：\n\n文件内容：\n{file_content}\n\n问题：{message}"

        # 保存用户消息
        add_message(db, session.id, "user", full_message)

        # 构建历史
        history = ChatService._build_history(db, session.id)

        # 调用 Agent
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_in_executor(
                None,
                enterprise_agent.chat,
                full_message,
                history,
            )
            response_result = asyncio.get_event_loop().run_until_complete(
                asyncio.wait_for(response, timeout=DEFAULT_TIMEOUT)
            )
        except ValueError as e:
            error_msg = str(e)
            if "未配置有效的模型" in error_msg or "未配置活跃的模型" in error_msg:
                error_content = "系统尚未配置AI模型，请联系管理员在管理端配置并启用模型后重试"
                add_message(db, session.id, "assistant", error_content)
                raise ModelNotConfiguredException()
            raise
        except asyncio.TimeoutError:
            add_message(db, session.id, "assistant", "请求超时，请稍后重试")
            raise TimeoutException()
        except Exception as e:
            logger.error(f"聊天处理异常: {str(e)}")
            add_message(db, session.id, "assistant", f"处理请求时发生错误: {str(e)}")
            raise

        # 保存助手回复
        add_message(db, session.id, "assistant", response_result)

        # 更新聊天次数
        if user:
            from app.db.crud import increment_chat_count
            increment_chat_count(db, user.id)
        else:
            increment_anonymous_chat_count(db)

        return {
            "session_id": session.id,
            "response": response_result,
        }

    @staticmethod
    def get_session_messages(db: Session, session_id: str) -> dict:
        """获取会话消息"""
        session = ChatService.get_session(db, session_id)
        messages = get_messages(db, session_id)
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat() + 'Z',
            "updated_at": session.updated_at.isoformat() + 'Z',
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() + 'Z',
                }
                for m in messages
            ],
        }

    @staticmethod
    def list_sessions(db: Session, user_id: str) -> list[dict]:
        """获取会话列表"""
        sessions = ChatService.get_user_sessions(db, user_id)
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat() + 'Z',
                "updated_at": s.updated_at.isoformat() + 'Z',
            }
            for s in sessions
        ]