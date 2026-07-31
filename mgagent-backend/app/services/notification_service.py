"""
通知服务层
"""
import requests

from app.config.config import settings
from app.core.logger import logger


class NotificationService:
    """通知服务"""

    @staticmethod
    def notify_new_user_registration(username: str, email: str) -> None:
        """通知管理员新用户注册"""
        try:
            requests.post(
                f"{settings.ADMIN_API_URL}/notifications/external",
                params={
                    "type": "user_registration",
                    "title": "新用户注册申请",
                    "message": f"用户 {username} ({email}) 提交了注册申请，请进行审批",
                },
                timeout=5,
            )
        except OSError as e:
            logger.warning(f"发送注册通知失败: {str(e)}")