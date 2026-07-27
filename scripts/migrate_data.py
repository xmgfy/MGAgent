#!/usr/bin/env python3
"""
数据迁移脚本
从 SQLite 迁移到 MySQL
从 ChromaDB 迁移到 Milvus
"""
import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "mgagent-backend"))
sys.path.insert(0, str(PROJECT_ROOT / "mgagent-admin-backend"))

# 配置
SQLITE_DB_PATH = PROJECT_ROOT / "mgagent-backend" / "data" / "chat.db"
CHROMA_PERSIST_DIR = PROJECT_ROOT / "mgagent-backend" / "data" / "chroma"

MYSQL_URL = "mysql+pymysql://mgagent:mgagent_password_2024@localhost:3306/mgagent?charset=utf8mb4"
MILVUS_HOST = "localhost"
MILVUS_PORT = 19530
MILVUS_COLLECTION = "mgagent_knowledge"


def migrate_sqlite_to_mysql():
    """从 SQLite 迁移到 MySQL"""
    print("=" * 60)
    print("📦 SQLite → MySQL 数据迁移")
    print("=" * 60)
    
    if not SQLITE_DB_PATH.exists():
        print(f"❌ SQLite 数据库不存在: {SQLITE_DB_PATH}")
        return False
    
    try:
        # 连接 SQLite
        sqlite_conn = sqlite3.connect(str(SQLITE_DB_PATH))
        sqlite_conn.row_factory = sqlite3.Row
        
        # 连接 MySQL
        from sqlalchemy import create_engine, text
        engine = create_engine(MYSQL_URL)
        
        tables = [
            "tenants", "admins", "admin_sessions", "model_configs",
            "system_notifications", "users", "chat_sessions",
            "chat_messages", "documents", "anonymous_stats"
        ]
        
        total_migrated = 0
        
        for table in tables:
            try:
                # 检查表是否存在
                cursor = sqlite_conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    print(f"  ⚠️  表 {table} 不存在，跳过")
                    continue
                
                # 读取数据
                rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
                if not rows:
                    print(f"  ⚠️  表 {table} 为空，跳过")
                    continue
                
                # 获取列名
                columns = [desc[0] for desc in sqlite_conn.execute(f"SELECT * FROM {table} LIMIT 1").description]
                
                # 插入数据到 MySQL
                with engine.connect() as mysql_conn:
                    for row in rows:
                        values = {}
                        for col in columns:
                            val = row[col]
                            if val is not None:
                                values[col] = val
                        
                        # 构建 INSERT 语句
                        placeholders = ", ".join([f":{col}" for col in values.keys()])
                        columns_str = ", ".join(values.keys())
                        insert_sql = f"INSERT IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"
                        
                        mysql_conn.execute(text(insert_sql), values)
                    
                    mysql_conn.commit()
                
                print(f"  ✅ 表 {table}: 已迁移 {len(rows)} 条记录")
                total_migrated += len(rows)
                
            except Exception as e:
                print(f"  ❌ 表 {table} 迁移失败: {e}")
                # 继续迁移其他表
                continue
        
        sqlite_conn.close()
        print(f"\n✅ SQLite → MySQL 迁移完成，共迁移 {total_migrated} 条记录")
        return True
        
    except Exception as e:
        print(f"❌ SQLite → MySQL 迁移失败: {e}")
        return False


def migrate_chroma_to_milvus():
    """从 ChromaDB 迁移到 Milvus"""
    print("\n" + "=" * 60)
    print("📦 ChromaDB → Milvus 数据迁移")
    print("=" * 60)
    
    if not CHROMA_PERSIST_DIR.exists():
        print(f"❌ ChromaDB 目录不存在: {CHROMA_PERSIST_DIR}")
        return False
    
    try:
        # 连接 ChromaDB
        from langchain_chroma import Chroma
        
        chroma_client = Chroma(persist_directory=str(CHROMA_PERSIST_DIR))
        chroma_collection = chroma_client._collection
        
        total_chunks = chroma_collection.count()
        if total_chunks == 0:
            print("⚠️  ChromaDB 为空，跳过")
            return True
        
        print(f"📊 ChromaDB 中共有 {total_chunks} 个向量块")
        
        # 获取所有数据
        all_data = chroma_collection.get(include=["documents", "metadatas", "embeddings"])
        
        if not all_data["ids"]:
            print("⚠️  ChromaDB 中没有数据，跳过")
            return True
        
        # 连接 Milvus
        from pymilvus import (
            connections, Collection, CollectionSchema,
            FieldSchema, DataType, utility
        )
        
        connections.connect(alias="default", host=MILVUS_HOST, port=str(MILVUS_PORT))
        
        # 创建集合
        if utility.has_collection(MILVUS_COLLECTION):
            collection = Collection(MILVUS_COLLECTION)
            collection.drop()
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="metadata", dtype=DataType.JSON),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=len(all_data["embeddings"][0]) if all_data["embeddings"] else 1536)
        ]
        
        schema = CollectionSchema(fields=fields, description="MGAgent 知识库向量集合")
        collection = Collection(name=MILVUS_COLLECTION, schema=schema)
        
        # 创建索引
        index_params = {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 1024}}
        collection.create_index(field_name="embedding", index_params=index_params)
        
        # 批量插入
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(all_data["ids"]), batch_size):
            batch_ids = all_data["ids"][i:i+batch_size]
            batch_contents = [doc[:65535] if doc else "" for doc in all_data["documents"][i:i+batch_size]]
            batch_metadata = all_data["metadatas"][i:i+batch_size]
            batch_embeddings = all_data["embeddings"][i:i+batch_size] if all_data["embeddings"] else [[0.0] * 1536] * len(batch_ids)
            
            data = [batch_ids, batch_contents, batch_metadata, batch_embeddings]
            collection.insert(data)
            total_inserted += len(batch_ids)
            print(f"  📥 已插入 {total_inserted}/{len(all_data['ids'])} 个向量块")
        
        collection.flush()
        collection.load()
        
        print(f"\n✅ ChromaDB → Milvus 迁移完成，共迁移 {total_inserted} 个向量块")
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB → Milvus 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 MGAgent 数据迁移工具")
    print(f"🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = True
    
    # 1. 迁移 SQLite 到 MySQL
    success &= migrate_sqlite_to_mysql()
    
    # 2. 迁移 ChromaDB 到 Milvus
    success &= migrate_chroma_to_milvus()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 数据迁移完成！")
    else:
        print("⚠️  数据迁移部分完成，请检查日志")
    print(f"🕐 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
