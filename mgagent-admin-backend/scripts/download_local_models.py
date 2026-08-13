#!/usr/bin/env python3
"""
本地模型下载脚本（Embedding + Reranker）
用于部署时预下载模型，避免在用户首次使用时下载导致卡顿

使用方法:
    # 下载 Embedding 模型
    python scripts/download_local_models.py --type embedding --model bge-small-zh

    # 下载 Reranker 模型
    python scripts/download_local_models.py --type reranker --model bge-reranker-v2-m3

    # 下载多个同类型模型
    python scripts/download_local_models.py --type reranker --models bge-reranker-v2-m3,bge-reranker-base

    # 下载所有类型的推荐模型
    python scripts/download_local_models.py --all

    # 列出所有可用模型（含 type 列）
    python scripts/download_local_models.py --list

    # 仅列出某类型
    python scripts/download_local_models.py --list --type reranker
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.local_models import (
    LOCAL_EMBEDDING_MODELS,
    LOCAL_RERANKER_MODELS,
    get_model_by_id as get_embedding_by_id,
    get_reranker_by_id,
)


def _set_hf_mirror():
    if not os.environ.get("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print(f"📡 使用镜像源: {os.environ['HF_ENDPOINT']}")


def _iter_models(model_type: str):
    if model_type == "embedding":
        for m in LOCAL_EMBEDDING_MODELS:
            yield m, "embedding"
    elif model_type == "reranker":
        for m in LOCAL_RERANKER_MODELS:
            yield m, "reranker"
    else:  # all
        for m in LOCAL_EMBEDDING_MODELS:
            yield m, "embedding"
        for m in LOCAL_RERANKER_MODELS:
            yield m, "reranker"


def _find_model(model_id: str):
    for m in LOCAL_EMBEDDING_MODELS:
        if m["id"] == model_id:
            return m, "embedding"
    for m in LOCAL_RERANKER_MODELS:
        if m["id"] == model_id:
            return m, "reranker"
    return None, None


def list_available_models(model_type: str = "all"):
    """列出所有可用模型"""
    models = list(_iter_models(model_type))
    print("\n" + "=" * 88)
    print(f"可用本地模型列表 ({model_type}) — 共 {len(models)} 个")
    print("=" * 88)
    print(f"{'类型':<10} {'ID':<28} {'模型名称':<45} {'大小':<10} {'语言':<12}")
    print("-" * 88)
    for model, mtype in models:
        print(f"{mtype:<10} {model['id']:<28} {model['name']:<45} {model['size_mb']:<8}MB  {model['language']:<12}")
    print("-" * 88)
    print("\n使用说明:")
    print("  列出所有: python scripts/download_local_models.py --list")
    print("  下载单个: python scripts/download_local_models.py --type reranker --model bge-reranker-v2-m3")
    print("  下载全部: python scripts/download_local_models.py --all")


def download_embedding(model_info: dict, cache_dir: str = None) -> bool:
    """下载 Embedding 模型（用 SentenceTransformer）"""
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface")
    _set_hf_mirror()

    print(f"\n📦 正在下载 Embedding 模型: {model_info['display_name']}")
    print(f"   HF 名称: {model_info['name']}")
    print(f"   向量维度: {model_info['dimension']}")
    print(f"   模型大小: ~{model_info['size_mb']}MB")
    print(f"   缓存目录: {cache_dir}")

    try:
        from sentence_transformers import SentenceTransformer

        os.makedirs(cache_dir, exist_ok=True)
        model = SentenceTransformer(model_info["name"], cache_folder=cache_dir)

        test_embedding = model.encode(["测试"], normalize_embeddings=True)
        actual_dim = len(test_embedding[0])

        print(f"\n✅ Embedding 模型下载成功！")
        print(f"   实际维度: {actual_dim}")
        if actual_dim != model_info["dimension"]:
            print(f"   ⚠️  注意: 实际维度 ({actual_dim}) 与预设值 ({model_info['dimension']}) 不符")
        return True

    except ImportError as e:
        print(f"\n❌ 缺少依赖: {e}")
        print("   请先安装: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if "timed out" in str(e).lower():
            print("   网络问题？已自动使用 hf-mirror.com 镜像")
        return False


def download_reranker(model_info: dict, cache_dir: str = None) -> bool:
    """下载 Reranker 模型（用 sentence-transformers CrossEncoder）"""
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface")
    _set_hf_mirror()

    print(f"\n📦 正在下载 Reranker 模型: {model_info['display_name']}")
    print(f"   HF 名称: {model_info['name']}")
    print(f"   最大序列长度: {model_info.get('max_length', 512)}")
    print(f"   模型大小: ~{model_info['size_mb']}MB")
    print(f"   缓存目录: {cache_dir}")

    try:
        from sentence_transformers import CrossEncoder

        os.makedirs(cache_dir, exist_ok=True)
        model = CrossEncoder(model_info["name"], cache_folder=cache_dir, num_labels=1)

        test_pairs = [("什么是向量数据库？", "向量数据库用于存储和检索向量嵌入。")]
        scores = model.predict(test_pairs)

        print(f"\n✅ Reranker 模型下载成功！")
        print(f"   测试对打分: {scores[0]:.4f}")
        return True

    except ImportError as e:
        print(f"\n❌ 缺少依赖: {e}")
        print("   请先安装: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if "timed out" in str(e).lower():
            print("   网络问题？已自动使用 hf-mirror.com 镜像")
        return False


def download_model(model_id: str, cache_dir: str = None) -> bool:
    """根据 ID 下载模型（自动识别 embedding / reranker）"""
    model_info, mtype = _find_model(model_id)
    if not model_info:
        print(f"❌ 模型 ID '{model_id}' 不存在，使用 --list 查看可用模型")
        return False

    if mtype == "embedding":
        return download_embedding(model_info, cache_dir)
    elif mtype == "reranker":
        return download_reranker(model_info, cache_dir)
    return False


def download_all(model_type: str = "all", cache_dir: str = None):
    """下载所有指定类型的模型"""
    models = list(_iter_models(model_type))
    print(f"\n🔄 开始下载所有本地模型 (type={model_type}) — 共 {len(models)} 个\n")

    success = 0
    failed = []
    for i, (info, mtype) in enumerate(models, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(models)}] ({mtype}) {info['display_name']}")
        print("=" * 70)
        if download_model(info["id"], cache_dir):
            success += 1
        else:
            failed.append(info["id"])

    print(f"\n{'='*70}")
    print(f"📊 下载完成: 成功 {success}/{len(models)}")
    if failed:
        print(f"⚠️  失败: {', '.join(failed)}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="下载本地 Embedding / Reranker 模型（部署时预缓存）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  列出可用模型:
    python scripts/download_local_models.py --list
    python scripts/download_local_models.py --list --type reranker

  下载单个模型 (自动识别类型):
    python scripts/download_local_models.py --model bge-small-zh
    python scripts/download_local_models.py --model bge-reranker-v2-m3

  批量下载 (自动识别类型):
    python scripts/download_local_models.py --models bge-small-zh,bge-reranker-v2-m3

  下载所有推荐模型:
    python scripts/download_local_models.py --all

  指定缓存目录 (Docker 部署时挂载卷):
    python scripts/download_local_models.py --all --cache-dir /opt/models/hf
        """,
    )

    parser.add_argument("--list", action="store_true", help="列出所有可用模型")
    parser.add_argument("--model", type=str, help="下载单个模型 (使用 --list 查看 ID)")
    parser.add_argument("--models", type=str, help="下载多个模型，逗号分隔 ID")
    parser.add_argument("--all", action="store_true", help="下载所有推荐模型")
    parser.add_argument("--type", type=str, default="all",
                        choices=["embedding", "reranker", "all"],
                        help="模型类型过滤 (默认 all)")
    parser.add_argument("--cache-dir", type=str, help="HF 缓存目录 (默认: ~/.cache/huggingface)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出 --list")

    args = parser.parse_args()

    if args.list:
        if args.json:
            data = {
                "embedding": LOCAL_EMBEDDING_MODELS,
                "reranker": LOCAL_RERANKER_MODELS,
            }
            if args.type != "all":
                data = {args.type: data[args.type]}
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            list_available_models(args.type)
        return

    if args.all:
        download_all(args.type, args.cache_dir)
        return

    if args.model:
        download_model(args.model, args.cache_dir)
        return

    if args.models:
        ids = [m.strip() for m in args.models.split(",") if m.strip()]
        print(f"\n🔄 开始下载 {len(ids)} 个模型\n")
        for mid in ids:
            download_model(mid, args.cache_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
