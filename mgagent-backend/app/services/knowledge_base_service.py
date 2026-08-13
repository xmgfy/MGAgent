"""
知识库管理服务 - 读取知识库配置、提供 CRUD
"""
from typing import Optional
from app.db import database as _db
from app.db.models import KnowledgeBase, Document


def _get_session():
    if _db.SessionLocal is None:
        _db.init_engine()
    return _db.SessionLocal()


def create_default_knowledge_base(db=None) -> Optional[KnowledgeBase]:
    """启动时确保存在一个默认知识库，把所有 knowledge_base_id IS NULL 的文档归入它"""
    session = db or _get_session()
    try:
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.name == "Default").first()
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
            session.add(kb)
            session.commit()

            # 把所有无归属的文档迁移到 Default
            orphan_docs = session.query(Document).filter(
                Document.knowledge_base_id.is_(None)
            ).all()
            for doc in orphan_docs:
                doc.knowledge_base_id = kb.id
            if orphan_docs:
                session.commit()

        return kb
    except Exception:
        session.rollback()
        raise
    finally:
        if db is None:
            session.close()


def get_knowledge_base(kb_id: str, db=None) -> Optional[KnowledgeBase]:
    session = db or _get_session()
    try:
        return session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    finally:
        if db is None:
            session.close()


def get_active_knowledge_bases(db=None) -> list[KnowledgeBase]:
    session = db or _get_session()
    try:
        return session.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True  # noqa: E712
        ).order_by(KnowledgeBase.created_at).all()
    finally:
        if db is None:
            session.close()


def get_document_knowledge_base(document_id: str, db=None) -> Optional[KnowledgeBase]:
    """获取文档归属的知识库"""
    session = db or _get_session()
    try:
        doc = session.query(Document).filter(Document.id == document_id).first()
        if doc and doc.knowledge_base_id:
            return get_knowledge_base(doc.knowledge_base_id, db=session)
        return None
    finally:
        if db is None:
            session.close()


def get_default_knowledge_base(db=None) -> KnowledgeBase:
    """获取默认知识库，不存在则创建"""
    return create_default_knowledge_base(db=db)


def _kb_to_dict(kb: KnowledgeBase) -> dict:
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
    }


def get_knowledge_base_config(kb_id: str) -> dict:
    """获取知识库配置 dict，用于 retriever / loader 等"""
    kb = get_knowledge_base(kb_id)
    if kb is None:
        kb = get_default_knowledge_base()
    return _kb_to_dict(kb)
