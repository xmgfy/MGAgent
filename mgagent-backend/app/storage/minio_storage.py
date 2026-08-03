"""
MinIO 对象存储实现 - MySQL 模式使用
"""
import io
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import quote

from minio import Minio
from minio.error import S3Error

from app.storage.base import BaseStorage
from app.config.config import get_minio_config


class MinioStorage(BaseStorage):
    """MinIO 对象存储"""
    
    def __init__(self):
        config = get_minio_config()
        self.bucket_name = config["bucket"]
        self.client = Minio(
            f"{config['host']}:{config['port']}",
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=False
        )
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
    
    def upload(self, file_name: str, file_data: bytes) -> str:
        """上传文件到 MinIO"""
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1]
        object_name = f"{file_id}{file_ext}"
        
        self.client.put_object(
            self.bucket_name,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=self._get_content_type(file_name)
        )
        
        return object_name
    
    def download(self, file_name: str) -> bytes:
        """从 MinIO 下载文件"""
        response = self.client.get_object(self.bucket_name, file_name)
        data = response.read()
        response.close()
        return data
    
    def delete(self, file_name: str) -> bool:
        """删除 MinIO 中的文件"""
        try:
            self.client.remove_object(self.bucket_name, file_name)
            return True
        except S3Error:
            return False
    
    def exists(self, file_name: str) -> bool:
        """检查 MinIO 中的文件是否存在"""
        try:
            self.client.stat_object(self.bucket_name, file_name)
            return True
        except S3Error:
            return False
    
    def list_files(self) -> List[Dict[str, Any]]:
        """列出 MinIO 存储桶中的所有文件"""
        files = []
        try:
            for obj in self.client.list_objects(self.bucket_name):
                files.append({
                    "name": obj.object_name,
                    "path": obj.object_name,
                    "size": obj.size,
                    "created_at": obj.last_modified.isoformat() if obj.last_modified else None,
                    "modified_at": obj.last_modified.isoformat() if obj.last_modified else None,
                })
        except S3Error:
            pass
        return files
    
    def get_file_info(self, file_name: str) -> Optional[Dict[str, Any]]:
        """获取 MinIO 中文件的信息"""
        try:
            stat = self.client.stat_object(self.bucket_name, file_name)
            return {
                "name": stat.object_name,
                "path": stat.object_name,
                "size": stat.size,
                "created_at": stat.last_modified.isoformat() if stat.last_modified else None,
                "modified_at": stat.last_modified.isoformat() if stat.last_modified else None,
            }
        except S3Error:
            return None
    
    def get_temp_path(self, file_name: str) -> str:
        """获取临时文件路径（用于处理后自动删除的场景）"""
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1]
        return f"temp_{file_id}{file_ext}"
    
    def _get_content_type(self, file_name: str) -> str:
        """根据文件扩展名获取 MIME 类型"""
        ext = os.path.splitext(file_name)[1].lower()
        content_types = {
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".json": "application/json",
            ".csv": "text/csv",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }
        return content_types.get(ext, "application/octet-stream")
