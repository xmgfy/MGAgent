"""
本地 Embedding 模型预设列表
用于前端下拉选择和自动填充维度
"""

LOCAL_EMBEDDING_MODELS = [
    {
        "id": "bge-small-zh",
        "name": "BAAI/bge-small-zh-v1.5",
        "display_name": "BGE Small (中文轻量)",
        "dimension": 512,
        "size_mb": 100,
        "language": "zh",
        "description": "轻量级中文 Embedding 模型，适合资源受限环境",
        "recommended_for": "调试、小规模知识库"
    },
    {
        "id": "bge-base-zh",
        "name": "BAAI/bge-base-zh-v1.5",
        "display_name": "BGE Base (中文均衡)",
        "dimension": 768,
        "size_mb": 400,
        "language": "zh",
        "description": "中文效果均衡，综合性能好",
        "recommended_for": "中等规模知识库"
    },
    {
        "id": "bge-large-zh",
        "name": "BAAI/bge-large-zh-v1.5",
        "display_name": "BGE Large (中文最佳)",
        "dimension": 1024,
        "size_mb": 1300,
        "language": "zh",
        "description": "中文 Embedding 效果最好，需要更多内存",
        "recommended_for": "大规模生产环境"
    },
    {
        "id": "bge-m3",
        "name": "BAAI/bge-m3",
        "display_name": "BGE M3 (多语言)",
        "dimension": 1024,
        "size_mb": 2300,
        "language": "zh+en",
        "description": "支持中英双语，多语言场景首选",
        "recommended_for": "中英文混合知识库"
    },
    {
        "id": "m3e-base",
        "name": "moka-ai/m3e-base",
        "display_name": "Moka M3E Base",
        "dimension": 768,
        "size_mb": 400,
        "language": "zh",
        "description": "开源社区常用中文模型",
        "recommended_for": "中等规模知识库"
    },
    {
        "id": "m3e-large",
        "name": "moka-ai/m3e-large",
        "display_name": "Moka M3E Large",
        "dimension": 1024,
        "size_mb": 1300,
        "language": "zh",
        "description": "中文大模型，效果优秀",
        "recommended_for": "大规模知识库"
    },
    {
        "id": "gte-base-zh",
        "name": "thenlper/gte-base-zh",
        "display_name": "GTE Base (阿里)",
        "dimension": 768,
        "size_mb": 400,
        "language": "zh",
        "description": "阿里达摩院出品",
        "recommended_for": "中等规模知识库"
    },
    {
        "id": "gte-large-zh",
        "name": "thenlper/gte-large-zh",
        "display_name": "GTE Large (阿里)",
        "dimension": 1024,
        "size_mb": 1300,
        "language": "zh",
        "description": "阿里达摩院出品大模型",
        "recommended_for": "大规模知识库"
    },
    {
        "id": "jina-embeddings-v2-base-zh",
        "name": "jinaai/jina-embeddings-v2-base-zh",
        "display_name": "Jina Embeddings V2 (中英)",
        "dimension": 768,
        "size_mb": 400,
        "language": "zh+en",
        "description": "中英双语模型",
        "recommended_for": "中英双语场景"
    },
    {
        "id": "paraphrase-multilingual",
        "name": "paraphrase-multilingual-MiniLM-L12-v2",
        "display_name": "MiniLM 多语言",
        "dimension": 384,
        "size_mb": 120,
        "language": "multi",
        "description": "多语言轻量模型，体积最小",
        "recommended_for": "多语言、资源受限"
    }
]


def get_local_models_list() -> list:
    """获取本地 Embedding 模型列表"""
    return LOCAL_EMBEDDING_MODELS


def get_model_by_id(model_id: str) -> dict | None:
    """根据 ID 获取模型信息"""
    for model in LOCAL_EMBEDDING_MODELS:
        if model["id"] == model_id:
            return model
    return None


def get_model_by_name(model_name: str) -> dict | None:
    """根据模型名称获取信息"""
    for model in LOCAL_EMBEDDING_MODELS:
        if model["name"] == model_name:
            return model
    return None
