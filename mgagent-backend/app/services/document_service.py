"""
文档服务层
"""
import os

from sqlalchemy.orm import Session

from app.db.crud import (
    create_document,
    get_document,
    get_documents,
    update_document_status,
    delete_document as delete_document_crud,
)
from app.db.models import Document
from app.core.logger import logger
from app.storage import get_storage
from app.rag.loader import DocumentLoader
from app.rag.retriever import get_vector_retriever
from app.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessException,
)

ALLOWED_EXTENSIONS = [".pdf", ".txt", ".docx", ".md"]


class DocumentService:
    """文档服务"""

    @staticmethod
    def upload_document(db: Session, filename: str, file_data: bytes) -> dict:
        """上传文档"""
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"不支持的文件格式，支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        storage = get_storage()
        stored_path = storage.upload(filename, file_data)
        file_size = len(file_data)

        document = create_document(db, filename, file_ext, file_size)
        logger.info(f"文档上传成功: {filename}, id: {document.id}, path: {stored_path}")

        # 尝试索引
        try:
            loader = DocumentLoader()
            
            # 对于本地存储，直接使用文件路径
            # 对于 MinIO 存储，需要先下载到临时文件
            if hasattr(storage, 'download'):
                try:
                    file_content = storage.download(stored_path)
                    temp_path = storage.get_temp_path(filename)
                    with open(temp_path, "wb") as f:
                        f.write(file_content)
                    docs = loader.load_file(temp_path)
                    # 清理临时文件
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    # 如果下载失败，尝试直接使用路径（本地存储场景）
                    docs = loader.load_file(stored_path)
            else:
                docs = loader.load_file(stored_path)
            
            get_vector_retriever().add_documents(docs)
            update_document_status(db, document.id, "indexed")
            logger.info(f"文档索引成功: {document.id}")
        except OSError as e:
            logger.error(f"文档索引失败: {str(e)}")
            update_document_status(db, document.id, "error")
            raise BusinessException(f"文档处理失败: {str(e)}")

        return _to_document_response(document)

    @staticmethod
    def list_documents(db: Session) -> list[dict]:
        """获取文档列表"""
        documents = get_documents(db)
        return [_to_document_response(d) for d in documents]

    @staticmethod
    def get_document_by_id(db: Session, document_id: str) -> dict:
        """获取单个文档"""
        document = get_document(db, document_id)
        if not document:
            raise NotFoundException("文档不存在")
        return _to_document_response(document)

    @staticmethod
    def delete_document(db: Session, document_id: str) -> None:
        """删除文档"""
        document = get_document(db, document_id)
        if not document:
            raise NotFoundException("文档不存在")
        
        # 删除关联的存储文件
        if delete_document_crud(db, document_id):
            logger.info(f"文档已删除: {document_id}")
        else:
            raise NotFoundException("文档不存在")


def _to_document_response(document: Document) -> dict:
    """转换为文档响应格式"""
    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status,
        "created_at": document.created_at.isoformat(),
    }