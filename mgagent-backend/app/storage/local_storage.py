"""
本地文件存储实现 - SQLite 模式使用
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.storage.base import BaseStorage
from app.config.config import get_document_dir


class LocalStorage(BaseStorage):
    """本地文件存储"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or get_document_dir()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload(self, file_name: str, file_data: bytes) -> str:
        """上传文件到本地存储"""
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1]
        stored_name = f"{file_id}{file_ext}"
        file_path = self.base_path / stored_name
        
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        return str(file_path)
    
    def download(self, file_name: str) -> bytes:
        """从本地存储下载文件"""
        file_path = Path(file_name)
        if not file_path.is_absolute():
            file_path = self.base_path / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_name}")
        
        with open(file_path, "rb") as f:
            return f.read()
    
    def delete(self, file_name: str) -> bool:
        """删除本地存储的文件"""
        file_path = Path(file_name)
        if not file_path.is_absolute():
            file_path = self.base_path / file_name
        
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
    
    def exists(self, file_name: str) -> bool:
        """检查本地存储的文件是否存在"""
        file_path = Path(file_name)
        if not file_path.is_absolute():
            file_path = self.base_path / file_name
        return file_path.exists()
    
    def list_files(self) -> List[Dict[str, Any]]:
        """列出本地存储的所有文件"""
        files = []
        if self.base_path.exists():
            for file_path in self.base_path.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
        return files
    
    def get_file_info(self, file_name: str) -> Optional[Dict[str, Any]]:
        """获取本地存储的文件信息"""
        file_path = Path(file_name)
        if not file_path.is_absolute():
            file_path = self.base_path / file_name
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    def get_temp_path(self, file_name: str) -> str:
        """获取临时文件路径"""
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1]
        temp_name = f"temp_{file_id}{file_ext}"
        return str(self.base_path / temp_name)
