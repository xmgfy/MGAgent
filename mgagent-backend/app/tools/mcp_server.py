from mcp import MCP, MCPConfig
from app.tools.calculator import calculate
from app.tools.sql_query import query_database, list_tables, describe_table
from app.rag.retriever import get_vector_retriever

mcp_config = MCPConfig(name="MGAgent MCP Server", version="1.0.0")

class MGAgentMCP(MCP):
    @MCP.tool("calculate", description="计算数学表达式")
    def calculate(self, expression: str) -> str:
        return calculate(expression)
    
    @MCP.tool("query_database", description="查询SQLite数据库")
    def query_database(self, query: str) -> str:
        return query_database(query)
    
    @MCP.tool("list_tables", description="获取数据库中的所有表名")
    def list_tables(self) -> str:
        return list_tables()
    
    @MCP.tool("describe_table", description="获取指定表的结构信息")
    def describe_table(self, table_name: str) -> str:
        return describe_table(table_name)
    
    @MCP.tool("rag_retrieve", description="检索知识库")
    def rag_retrieve(self, query: str) -> str:
        docs = get_vector_retriever().search(query, k=3)
        if not docs:
            return "未找到相关文档"
        
        context = "\n\n".join([f"【{doc.metadata.get('source', '未知文档')}】\n{doc.page_content}" for doc in docs])
        return f"检索到以下相关文档内容：\n\n{context}"

if __name__ == "__main__":
    mcp = MGAgentMCP(config=mcp_config)
    mcp.serve()