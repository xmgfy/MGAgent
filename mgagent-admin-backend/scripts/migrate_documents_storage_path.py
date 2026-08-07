"""
数据库迁移脚本 - 为 documents 表添加 storage_path 列
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config.settings import settings


def migrate():
    """执行迁移"""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查 storage_path 列是否已存在
            result = conn.execute(text("DESCRIBE documents"))
            columns = [row[0] for row in result.fetchall()]
            
            if 'storage_path' in columns:
                print("storage_path 列已存在，跳过添加")
                return True
            
            # 添加 storage_path 列
            conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN storage_path VARCHAR(500) NULL 
                COMMENT 'MinIO 对象名或本地路径'
            """))
            conn.commit()
            
            print("storage_path 列添加成功")
            return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
