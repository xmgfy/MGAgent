from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sqlite3
from app.db.database import get_db
from app.db.models import Admin
from .auth import get_current_admin

router = APIRouter()

class StorageDBStats(BaseModel):
    database_path: str
    tables: List[str]
    total_records: Dict[str, int]

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
        from app.db.database import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        total_records = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_records[table] = cursor.fetchone()[0]
        
        conn.close()
        
        return StorageDBStats(
            database_path=str(DB_PATH),
            tables=tables,
            total_records=total_records
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage-db/tables", response_model=List[TableInfo])
async def list_tables(admin: Admin = Depends(get_current_admin)):
    try:
        from app.db.database import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info_list = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            record_count = cursor.fetchone()[0]
            
            column_list = []
            for col in columns:
                column_list.append({
                    "name": col[1],
                    "type": col[2],
                    "is_pk": bool(col[5])
                })
            
            table_info_list.append(TableInfo(
                name=table,
                columns=column_list,
                record_count=record_count
            ))
        
        conn.close()
        
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
        from app.db.database import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="表不存在")
        
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {"columns": columns, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage-db/query")
async def execute_query(
    request: QueryRequest,
    admin: Admin = Depends(get_current_admin)
):
    try:
        from app.db.database import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(request.query)
        
        if request.query.strip().lower().startswith('select'):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            result = {"columns": columns, "data": data}
        else:
            conn.commit()
            result = {"message": f"执行成功，影响 {cursor.rowcount} 行"}
        
        conn.close()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
