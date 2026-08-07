#!/usr/bin/env python3
"""
本地 Embedding 模型下载脚本
用于部署时预下载模型，避免在用户首次使用时下载导致卡顿

使用方法:
    # 下载单个模型
    python scripts/download_local_models.py --model bge-small-zh
    
    # 下载多个模型
    python scripts/download_local_models.py --models bge-small-zh,bge-large-zh
    
    # 下载所有推荐模型
    python scripts/download_local_models.py --all
    
    # 列出所有可用模型
    python scripts/download_local_models.py --list
    
    # 指定缓存目录
    python scripts/download_local_models.py --model bge-small-zh --cache-dir /path/to/cache
"""

import os
import sys
import argparse
import json

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.local_models import LOCAL_EMBEDDING_MODELS, get_model_by_id


def list_available_models():
    """列出所有可用模型"""
    print("\n" + "=" * 70)
    print("可用的本地 Embedding 模型列表")
    print("=" * 70)
    print(f"{'ID':<25} {'模型名称':<40} {'维度':<8} {'大小':<10} {'语言':<10}")
    print("-" * 70)
    
    for model in LOCAL_EMBEDDING_MODELS:
        print(f"{model['id']:<25} {model['name']:<40} {model['dimension']:<8} {model['size_mb']:<10} {model['language']:<10}")
    
    print("-" * 70)
    print(f"\n共 {len(LOCAL_EMBEDDING_MODELS)} 个模型可选")
    print("\n使用说明:")
    print("  python scripts/download_local_models.py --model <ID>")
    print("  python scripts/download_local_models.py --all")


def download_model(model_id: str, cache_dir: str = None):
    """下载指定模型"""
    model_info = get_model_by_id(model_id)
    if not model_info:
        print(f"❌ 模型 ID '{model_id}' 不存在，请使用 --list 查看可用模型")
        return False
    
    # 设置缓存目录
    if cache_dir is None:
        cache_dir = os.path.expanduser("~/.cache/huggingface")
    
    # 设置 HuggingFace 镜像源（国内网络必需）
    if not os.environ.get("HF_ENDPOINT"):
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print(f"📡 使用镜像源: {os.environ['HF_ENDPOINT']}")
    
    print(f"\n📦 正在下载模型: {model_info['display_name']}")
    print(f"   模型名称: {model_info['name']}")
    print(f"   向量维度: {model_info['dimension']}")
    print(f"   模型大小: ~{model_info['size_mb']}MB")
    print(f"   缓存目录: {cache_dir}")
    print()
    
    try:
        from sentence_transformers import SentenceTransformer
        
        os.makedirs(cache_dir, exist_ok=True)
        
        model = SentenceTransformer(model_info["name"], cache_folder=cache_dir)
        
        # 验证模型
        test_embedding = model.encode(["测试"], normalize_embeddings=True)
        actual_dim = len(test_embedding[0])
        
        print(f"\n✅ 模型下载成功！")
        print(f"   实际维度: {actual_dim}")
        
        if actual_dim != model_info["dimension"]:
            print(f"   ⚠️  注意: 实际维度 ({actual_dim}) 与预设值 ({model_info['dimension']}) 不符")
            print(f"   请在配置时填写正确的维度: {actual_dim}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ 缺少依赖: {e}")
        print("   请先安装: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if "timed out" in str(e).lower():
            print("   可能是网络问题，已自动使用 hf-mirror.com 镜像")
            print("   如需手动设置镜像: export HF_ENDPOINT=https://hf-mirror.com")
        return False


def download_all_models(cache_dir: str = None):
    """下载所有模型"""
    print("\n🔄 开始下载所有本地 Embedding 模型\n")
    
    success_count = 0
    failed_models = []
    
    for i, model in enumerate(LOCAL_EMBEDDING_MODELS, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(LOCAL_EMBEDDING_MODELS)}] 下载: {model['display_name']}")
        print("="*60)
        
        if download_model(model["id"], cache_dir):
            success_count += 1
        else:
            failed_models.append(model["id"])
    
    print(f"\n{'='*60}")
    print(f"📊 下载完成: 成功 {success_count}/{len(LOCAL_EMBEDDING_MODELS)}")
    if failed_models:
        print(f"⚠️  失败的模型: {', '.join(failed_models)}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="下载本地 Embedding 模型（部署时使用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  列出可用模型:
    python scripts/download_local_models.py --list
    
  下载单个模型:
    python scripts/download_local_models.py --model bge-small-zh
    
  下载多个模型:
    python scripts/download_local_models.py --models bge-small-zh,bge-large-zh
    
  下载所有模型:
    python scripts/download_local_models.py --all
    
  指定缓存目录:
    python scripts/download_local_models.py --model bge-small-zh --cache-dir /opt/models/hf
        """
    )
    
    parser.add_argument("--list", action="store_true", help="列出所有可用模型")
    parser.add_argument("--model", type=str, help="下载单个模型 (使用 --list 查看 ID)")
    parser.add_argument("--models", type=str, help="下载多个模型，用逗号分隔 ID")
    parser.add_argument("--all", action="store_true", help="下载所有推荐模型")
    parser.add_argument("--cache-dir", type=str, help="指定缓存目录 (默认: ~/.cache/huggingface)")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出列表")
    
    args = parser.parse_args()
    
    if args.list:
        if args.json:
            print(json.dumps(LOCAL_EMBEDDING_MODELS, indent=2, ensure_ascii=False))
        else:
            list_available_models()
        return
    
    if args.all:
        download_all_models(args.cache_dir)
        return
    
    if args.model:
        download_model(args.model, args.cache_dir)
        return
    
    if args.models:
        model_ids = [m.strip() for m in args.models.split(",")]
        print(f"\n🔄 开始下载 {len(model_ids)} 个模型")
        
        for model_id in model_ids:
            print(f"\n{'='*60}")
            download_model(model_id, args.cache_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
