"""
SQL 查询工具 - 仅允许只读查询
支持 SQLite 和 MySQL
"""
import re
import sqlite3
from typing import Optional

from app.config.config import settings, is_mysql_scheme


# 危险 SQL 模式（黑名单）
DANGEROUS_PATTERNS = [
    r'\bDROP\b',
    r'\bDELETE\b',
    r'\bUPDATE\b',
    r'\bINSERT\b',
    r'\bALTER\b',
    r'\bCREATE\b',
    r'\bTRUNCATE\b',
    r'\bEXEC\b',
    r'\bEXECUTE\b',
    r';.*--',  # SQL 注入
    r'/\*.*?\*/',  # 注释
]


def _is_safe_query(query: str) -> bool:
    """
    检查 SQL 查询是否安全（仅允许 SELECT）
    
    Args:
        query: SQL 查询语句
        
    Returns:
        是否安全
    """
    query = query.strip()
    
    # 必须以 SELECT 开头
    if not query.lower().startswith('select'):
        return False
    
    # 检查是否包含危险关键字
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    
    # 禁止多语句执行
    if ';' in query.rstrip(';'):
        return False
    
    return True


def query_database(query: str) -> str:
    """
    查询数据库（仅支持 SELECT 语句）
    支持 SQLite 和 MySQL
    
    Args:
        query: SQL SELECT 查询语句
        
    Returns:
        查询结果或错误信息
    """
    try:
        if not _is_safe_query(query):
            return "安全错误：仅允许执行 SELECT 查询语句，禁止任何修改操作"
        
        if is_mysql_scheme():
            # MySQL 模式
            import pymysql
            conn = pymysql.connect(
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE,
                charset='utf8mb4'
            )
        else:
            # SQLite 模式
            conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
            conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        
        # 限制返回结果数量，防止数据泄露
        if len(result) > 100:
            result = result[:100]
            return f"查询结果（已限制为前100条，共{len(result)}条）:\n{result}"
        
        return f"查询结果:\n{result}"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()


def list_tables() -> str:
    """
    获取数据库中的所有表名（受限版本）
    
    Returns:
        表名列表（脱敏）
    """
    try:
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        cursor = conn.cursor()
        
        # 只返回白名单中的表，避免泄露敏感表信息
        allowed_tables = [
            'users', 'chat_sessions', 'chat_messages', 
            'documents', 'model_configs'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # 过滤掉系统表和敏感表
        safe_tables = [t for t in all_tables if t in allowed_tables]
        
        return f"可查询的业务表:\n{', '.join(safe_tables)}"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()


def describe_table(table_name: str) -> str:
    """
    获取指定表的结构信息（受限版本）
    
    Args:
        table_name: 表名
        
    Returns:
        表结构信息（脱敏）
    """
    try:
        # 白名单：允许查询的表和其允许展示的字段
        allowed_schemas = {
            'users': ['id', 'username', 'email', 'role', 'status', 'created_at'],
            'chat_sessions': ['id', 'title', 'created_at'],
            'chat_messages': ['id', 'session_id', 'role', 'created_at'],
            'documents': ['id', 'filename', 'file_type', 'file_size', 'status', 'created_at'],
            'model_configs': ['id', 'name', 'model_name', 'is_active']
        }
        
        if table_name not in allowed_schemas:
            return f"表 {table_name} 不在允许查询的范围内"
        
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        allowed_cols = allowed_schemas[table_name]
        result = f"表 {table_name} 的可查询字段:\n"
        for col in columns:
            if col[1] in allowed_cols:
                result += f"- {col[1]}: {col[2]}\n"
        
        return result
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()
