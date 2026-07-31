"""
异常层次体系
"""
from typing import Optional


class BusinessException(Exception):
    """业务异常基类"""
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "内部错误",
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        self.message = message
        if code:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(BusinessException):
    """资源不存在"""
    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message)


class UnauthorizedException(BusinessException):
    """未授权"""
    status_code = 401
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "未授权访问"):
        super().__init__(message)


class ForbiddenException(BusinessException):
    """禁止访问"""
    status_code = 403
    code = "FORBIDDEN"

    def __init__(self, message: str = "禁止访问"):
        super().__init__(message)


class ValidationException(BusinessException):
    """参数校验失败"""
    status_code = 400
    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message)


class ModelNotConfiguredException(BusinessException):
    """模型未配置"""
    status_code = 503
    code = "MODEL_NOT_CONFIGURED"

    def __init__(self, message: str = "系统尚未配置AI模型"):
        super().__init__(message)


class ChatLimitExceededException(BusinessException):
    """聊天次数超限"""
    status_code = 403
    code = "CHAT_LIMIT_EXCEEDED"

    def __init__(self, message: str = "已达到最大问答次数限制"):
        super().__init__(message)


class TimeoutException(BusinessException):
    """请求超时"""
    status_code = 504
    code = "TIMEOUT"

    def __init__(self, message: str = "请求超时，请稍后重试"):
        super().__init__(message)
