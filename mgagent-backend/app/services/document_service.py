"""
文档服务层
"""
import os
import uuid

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
from app.config.config import get_document_dir
from app.rag.loader import DocumentLoader
from app.rag.retriever import get_vector_retriever
from app.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessException,
)

DOCUMENT_DIR = get_document_dir()
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

        file_id = str(uuid.uuid4())
        file_path = os.path.join(DOCUMENT_DIR, f"{file_id}{file_ext}")

        with open(file_path, "wb") as f:
            f.write(file_data)

        document = create_document(db, filename, file_ext, os.path.getsize(file_path))
        logger.info(f"文档上传成功: {filename}, id: {document.id}")

        # 尝试索引
        try:
            loader = DocumentLoader()
            docs = loader.load_file(file_path)
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
        if not delete_document_crud(db, document_id):
            raise NotFoundException("文档不存在")
        logger.info(f"文档已删除: {document_id}")


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