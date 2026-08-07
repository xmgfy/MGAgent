from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db, init_engine
from app.db.models import Admin
from app.config.config import is_sqlite_scheme, get_sqlite_path, get_database_url
from .auth import get_current_admin

router = APIRouter()

def get_ensure_engine():
    """确保数据库引擎已初始化"""
    from app.db.database import engine
    if engine is None:
        return init_engine()
    return engine

class StorageDBStats(BaseModel):
    database_path: str
    tables: List[str]
    total_records: Dict[str, int]
    database_type: str

class ColumnInfo(BaseModel):
    name: str
    type: str
    is_pk: bool

class TableInfo(BaseModel):
    name: str
    columns: List[ColumnInfo]
    record_count: int

class QueryRequest(BaseModel):
    query: str

@router.get("/storage-db/stats", response_model=StorageDBStats)
async def get_storage_db_stats(admin: Admin = Depends(get_current_admin)):
    try:
        eng = get_ensure_engine()
        with eng.connect() as conn:
            inspector = inspect(eng)
            tables = inspector.get_table_names()
            
            total_records = {}
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                    total_records[table] = result.scalar()
                except Exception:
                    total_records[table] = 0
        
        db_type = "sqlite" if is_sqlite_scheme() else "mysql"
        db_path = str(get_sqlite_path()) if is_sqlite_scheme() else get_database_url()
        
        return StorageDBStats(
            database_path=db_path,
            tables=tables,
            total_records=total_records,
            database_type=db_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/tables", response_model=List[TableInfo])
async def list_tables(admin: Admin = Depends(get_current_admin)):
    try:
        eng = get_ensure_engine()
        inspector = inspect(eng)
        tables = inspector.get_table_names()
        
        table_info_list = []
        for table in tables:
            columns = inspector.get_columns(table)
            pk_cols = inspector.get_pk_constraint(table)
            pk_columns = pk_cols['constrained_columns'] if pk_cols else []
            
            try:
                with eng.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                    record_count = result.scalar()
            except Exception:
                record_count = 0
            
            column_list = []
            for col in columns:
                column_list.append(ColumnInfo(
                    name=col['name'],
                    type=str(col['type']),
                    is_pk=col['name'] in pk_columns
                ))
            
            table_info_list.append(TableInfo(
                name=table,
                columns=column_list,
                record_count=record_count
            ))
        
        return table_info_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    limit: int = 50,
    offset: int = 0,
    admin: Admin = Depends(get_current_admin)
):
    try:
        eng = get_ensure_engine()
        inspector = inspect(eng)
        tables = inspector.get_table_names()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail="表不存在")
        
        with eng.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM `{table_name}` LIMIT :limit OFFSET :offset"), {"limit": limit, "offset": offset})
            columns = list(result.keys())
            rows = result.fetchall()
        
        data = []
        for row in rows:
            data.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
        
        return {"columns": columns, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage-db/query")
async def execute_query(
    request: QueryRequest,
    admin: Admin = Depends(get_current_admin)
):
    conn = None
    try:
        eng = get_ensure_engine()
        query = request.query.strip()
        
        # 安全检查：禁止危险操作
        dangerous_keywords = ['drop', 'truncate', 'delete', 'alter']
        query_lower = query.lower()
        for kw in dangerous_keywords:
            if query_lower.startswith(kw):
                raise HTTPException(status_code=403, detail=f"禁止执行 {kw.upper()} 操作")

        conn = eng.connect()
        result = conn.execute(text(query))
        
        if query_lower.startswith('select') or query_lower.startswith('show') or query_lower.startswith('describe') or query_lower.startswith('explain'):
            columns = list(result.keys())
            rows = result.fetchall()
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, [str(v) if v is not None else None for v in row])))
            
            conn.close()
            return {"columns": columns, "data": data}
        else:
            conn.commit()
            conn.close()
            return {"message": f"执行成功，影响 {result.rowcount} 行"}
    except HTTPException:
        if conn:
            conn.close()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=str(e))
