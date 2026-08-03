"""
存储接口基类 - 定义统一的文件存储操作
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path


class BaseStorage(ABC):
    """文件存储抽象基类"""
    
    @abstractmethod
    def upload(self, file_name: str, file_data: bytes) -> str:
        """
        上传文件，返回文件路径/对象key
        
        Args:
            file_name: 文件名（含扩展名）
            file_data: 文件二进制数据
            
        Returns:
            文件存储路径或对象key
        """
        pass
    
    @abstractmethod
    def download(self, file_name: str) -> bytes:
        """
        下载文件
        
        Args:
            file_name: 文件名或对象key
            
        Returns:
            文件二进制数据
        """
        pass
    
    @abstractmethod
    def delete(self, file_name: str) -> bool:
        """
        删除文件
        
        Args:
            file_name: 文件名或对象key
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(self, file_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_name: 文件名或对象key
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def list_files(self) -> List[Dict[str, Any]]:
        """
        列出所有文件
        
        Returns:
            文件信息列表，每个文件包含 name, size, created_at 等信息
        """
        pass
    
    @abstractmethod
    def get_file_info(self, file_name: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_name: 文件名或对象key
            
        Returns:
            文件信息字典或 None
        """
        pass
    
    @abstractmethod
    def get_temp_path(self, file_name: str) -> str:
        """
        获取临时文件路径（用于处理后自动删除的场景）
        
        Args:
            file_name: 文件名或对象key
            
        Returns:
            临时文件路径
        """
        pass
