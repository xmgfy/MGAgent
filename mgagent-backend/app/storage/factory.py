"""
存储工厂 (MySQL + MinIO only)
"""
from app.storage.base import BaseStorage
from app.storage.local_storage import LocalStorage


_storage_instance: BaseStorage | None = None


def get_storage() -> BaseStorage:
    """
    获取存储实例：优先 MinIO，失败降级为本地存储
    """
    global _storage_instance
    
    if _storage_instance is not None:
        return _storage_instance
    
    try:
        from app.storage.minio_storage import MinioStorage
        _storage_instance = MinioStorage()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"MinIO 初始化失败，降级为本地存储: {e}")
        _storage_instance = LocalStorage()
    
    return _storage_instance


def reset_storage() -> None:
    """重置存储实例"""
    global _storage_instance
    _storage_instance = None
