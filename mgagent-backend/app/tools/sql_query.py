"""
SQL 查询工具 - MySQL only
仅允许只读查询
"""
import re
from typing import Optional

from app.config.config import settings


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
    r';.*--',
    r'/\*.*?\*/',
]


def _is_safe_query(query: str) -> bool:
    query = query.strip()
    if not query.lower().startswith('select'):
        return False
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    if ';' in query.rstrip(';'):
        return False
    return True


def _connect():
    import pymysql
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset='utf8mb4',
    )


def query_database(query: str) -> str:
    """查询数据库（仅支持 SELECT 语句）"""
    conn = None
    try:
        if not _is_safe_query(query):
            return "安全错误：仅允许执行 SELECT 查询语句，禁止任何修改操作"

        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(query)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        result = [dict(zip(columns, row)) for row in rows]

        if len(result) > 100:
            result = result[:100]
            return f"查询结果（已限制为前100条）:\n{result}"

        return f"查询结果:\n{result}"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        if conn:
            conn.close()


def list_tables() -> str:
    """获取数据库中业务相关的表名（白名单）"""
    conn = None
    try:
        conn = _connect()
        cursor = conn.cursor()
        allowed_tables = {'users', 'chat_sessions', 'chat_messages', 'documents', 'model_configs'}

        cursor.execute("SHOW TABLES")
        all_tables = [row[0] for row in cursor.fetchall()]

        safe_tables = [t for t in all_tables if t in allowed_tables]
        return f"可查询的业务表:\n{', '.join(safe_tables)}"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        if conn:
            conn.close()


def describe_table(table_name: str) -> str:
    """获取指定表的结构信息（白名单+脱敏）"""
    conn = None
    try:
        allowed_schemas = {
            'users': ['id', 'username', 'email', 'role', 'status', 'created_at'],
            'chat_sessions': ['id', 'title', 'created_at'],
            'chat_messages': ['id', 'session_id', 'role', 'created_at'],
            'documents': ['id', 'filename', 'file_type', 'file_size', 'status', 'created_at'],
            'model_configs': ['id', 'name', 'model_name', 'is_active'],
        }
        if table_name not in allowed_schemas:
            return f"表 {table_name} 不在允许查询的范围内"

        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()

        allowed_cols = allowed_schemas[table_name]
        result = f"表 {table_name} 的可查询字段:\n"
        for col in columns:
            if col[0] in allowed_cols:
                result += f"- {col[0]}: {col[1]}\n"
        return result
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        if conn:
            conn.close()
