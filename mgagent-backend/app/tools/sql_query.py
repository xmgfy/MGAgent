import sqlite3
from app.config.settings import settings

def query_database(query: str) -> str:
    try:
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().lower().startswith('select'):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))
            
            return f"查询结果:\n{result}"
        else:
            conn.commit()
            return f"执行成功，影响 {cursor.rowcount} 行"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()

def list_tables() -> str:
    try:
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        return f"数据库中的表:\n{', '.join(tables)}"
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()

def describe_table(table_name: str) -> str:
    try:
        conn = sqlite3.connect(settings.DATABASE_URL.replace("sqlite:///", ""))
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        result = f"表 {table_name} 的结构:\n"
        for col in columns:
            result += f"- {col[1]}: {col[2]} (主键: {'是' if col[5] else '否'})\n"
        
        return result
    except Exception as e:
        return f"查询错误: {str(e)}"
    finally:
        conn.close()