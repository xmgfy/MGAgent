"""
存储工厂 - 根据配置创建对应的存储实例
"""
import logging

from app.storage.base import BaseStorage
from app.storage.local_storage import LocalStorage
from app.config.config import is_mysql_scheme


_storage_instance: BaseStorage | None = None


def get_storage() -> BaseStorage:
    """
    获取当前模式下的存储实例
    
    Returns:
        BaseStorage 实例（LocalStorage 或 MinioStorage）
    """
    global _storage_instance
    
    if _storage_instance is not None:
        return _storage_instance
    
    if is_mysql_scheme():
        try:
            from app.storage.minio_storage import MinioStorage
            _storage_instance = MinioStorage()
            logging.getLogger(__name__).info("使用 MinIO 对象存储")
        except Exception as e:
            logging.getLogger(__name__).warning(f"MinIO 初始化失败，降级为本地存储: {e}")
            _storage_instance = LocalStorage()
    else:
        _storage_instance = LocalStorage()
    
    return _storage_instance


def reset_storage() -> None:
    """重置存储实例（用于测试或配置变更后）"""
    global _storage_instance
    _storage_instance = None
