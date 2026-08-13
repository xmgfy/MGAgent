"""
知识库 CRUD - Admin Backend
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import KnowledgeBase, Document


def _row_to_dict(kb: KnowledgeBase) -> dict:
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "tenant_id": kb.tenant_id,
        "vector_db_type": kb.vector_db_type,
        "embedding_model_id": kb.embedding_model_id,
        "chunk_size": kb.chunk_size,
        "chunk_overlap": kb.chunk_overlap,
        "chunk_separator": kb.chunk_separator,
        "retrieve_limit": kb.retrieve_limit,
        "similarity_threshold": kb.similarity_threshold,
        "enable_rerank": kb.enable_rerank,
        "rerank_model_id": kb.rerank_model_id,
        "rerank_top_n": kb.rerank_top_n,
        "rerank_score_threshold": kb.rerank_score_threshold,
        "enable_hybrid": kb.enable_hybrid,
        "hybrid_alpha": kb.hybrid_alpha,
        "is_active": kb.is_active,
        "created_at": kb.created_at.isoformat() if kb.created_at else None,
        "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
    }


def list_knowledge_bases(db: Session, tenant_id: Optional[str] = None) -> list[dict]:
    query = db.query(KnowledgeBase)
    if tenant_id:
        query = query.filter(KnowledgeBase.tenant_id == tenant_id)
    results = query.order_by(KnowledgeBase.created_at).all()

    kb_dicts = [_row_to_dict(kb) for kb in results]
    # 附加文档数
    for kb_dict in kb_dicts:
        count = db.query(Document).filter(
            Document.knowledge_base_id == kb_dict["id"]
        ).count()
        kb_dict["document_count"] = count
    return kb_dicts


def get_knowledge_base(db: Session, kb_id: str) -> Optional[dict]:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        return None
    result = _row_to_dict(kb)
    result["document_count"] = db.query(Document).filter(
        Document.knowledge_base_id == kb_id
    ).count()
    return result


def get_knowledge_base_row(db: Session, kb_id: str) -> Optional[KnowledgeBase]:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()


def create_knowledge_base(db: Session, data: dict) -> dict:
    import uuid
    kb = KnowledgeBase(
        id=str(uuid.uuid4()),
        name=data.get("name", ""),
        description=data.get("description"),
        tenant_id=data.get("tenant_id"),
        vector_db_type=data.get("vector_db_type", "default"),
        embedding_model_id=data.get("embedding_model_id"),
        chunk_size=data.get("chunk_size", 500),
        chunk_overlap=data.get("chunk_overlap", 50),
        chunk_separator=data.get("chunk_separator"),
        retrieve_limit=data.get("retrieve_limit", 5),
        similarity_threshold=data.get("similarity_threshold"),
        enable_rerank=data.get("enable_rerank", False),
        rerank_model_id=data.get("rerank_model_id"),
        rerank_top_n=data.get("rerank_top_n", 3),
        rerank_score_threshold=data.get("rerank_score_threshold"),
        enable_hybrid=data.get("enable_hybrid", False),
        hybrid_alpha=data.get("hybrid_alpha", 0.7),
        is_active=data.get("is_active", True),
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return _row_to_dict(kb)


def update_knowledge_base(db: Session, kb_id: str, data: dict) -> Optional[dict]:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        return None
    updatable = [
        "name", "description", "vector_db_type", "embedding_model_id",
        "chunk_size", "chunk_overlap", "chunk_separator",
        "retrieve_limit", "similarity_threshold",
        "enable_rerank", "rerank_model_id", "rerank_top_n", "rerank_score_threshold",
        "enable_hybrid", "hybrid_alpha", "is_active",
    ]
    for field in updatable:
        if field in data:
            setattr(kb, field, data[field])
    db.commit()
    db.refresh(kb)
    return _row_to_dict(kb)


def delete_knowledge_base(db: Session, kb_id: str) -> bool:
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if kb is None:
        return False
    # 不能删 Default
    if kb.name == "Default":
        raise ValueError("Default 知识库不可删除")
    # 先把该库下所有文档移到 Default
    default_kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == "Default").first()
    docs = db.query(Document).filter(Document.knowledge_base_id == kb_id).all()
    for doc in docs:
        doc.knowledge_base_id = default_kb.id if default_kb else None
    db.delete(kb)
    db.commit()
    return True


def ensure_default_knowledge_base(db: Session) -> KnowledgeBase:
    """确保 Default 知识库存在，迁移所有无归属文档"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.name == "Default").first()
    if kb is None:
        import uuid
        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            name="Default",
            description="默认知识库 - 自动迁移历史文档至此",
            is_active=True,
            chunk_size=500,
            chunk_overlap=50,
            retrieve_limit=5,
            enable_rerank=False,
            rerank_top_n=3,
            enable_hybrid=False,
            hybrid_alpha=0.7,
        )
        db.add(kb)
        db.flush()

        orphan_docs = db.query(Document).filter(Document.knowledge_base_id.is_(None)).all()
        for doc in orphan_docs:
            doc.knowledge_base_id = kb.id
        db.commit()
        db.refresh(kb)
    return kb
