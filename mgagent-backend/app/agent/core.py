from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from typing import List, Dict, Optional
from datetime import datetime
from app.config.settings import settings, get_active_model_config
from app.rag.retriever import get_vector_retriever
from app.tools.calculator import calculate
from app.tools.sql_query import query_database, list_tables, describe_table
import json

def create_llm():
    """根据配置创建LLM实例，必须使用admin端配置的模型"""
    model_config = get_active_model_config()
    
    if model_config and model_config.get('api_key') and model_config.get('api_base') and model_config.get('model_name'):
        return ChatOpenAI(
            model=model_config['model_name'],
            api_key=model_config['api_key'],
            base_url=model_config['api_base'],
            temperature=0.1
        )
    
    raise ValueError("未配置有效的模型，请在admin管理端配置并启用模型")

def get_llm():
    """每次调用时动态获取最新的LLM实例"""
    return create_llm()

class EnterpriseAgent:
    def __init__(self):
        self.tools = {
            "rag_retrieve": {
                "function": self._rag_retrieve,
                "description": "检索企业知识库，用于查找公司政策、产品文档、流程规范等信息"
            },
            "calculate": {
                "function": calculate,
                "description": "计算数学表达式，用于处理数值计算问题"
            },
            "query_database": {
                "function": query_database,
                "description": "查询SQLite数据库，用于获取业务数据"
            },
            "list_tables": {
                "function": list_tables,
                "description": "获取数据库中的所有表名"
            },
            "describe_table": {
                "function": describe_table,
                "description": "获取指定表的结构信息"
            }
        }
    
    def _rag_retrieve(self, query: str) -> str:
        docs = get_vector_retriever().search(query, k=3)
        if not docs:
            return "未找到相关文档"
        
        context = "\n\n".join([f"【{doc.metadata.get('source', '未知文档')}】\n{doc.page_content}" for doc in docs])
        
        return f"检索到以下相关文档内容：\n\n{context}"
    
    def _build_tool_prompt(self) -> str:
        tool_list = []
        for name, info in self.tools.items():
            tool_list.append(f"- {name}: {info['description']}")
        return "\n".join(tool_list)
    
    def _parse_tool_call(self, response: str) -> Optional[Dict]:
        try:
            lines = response.strip().split("\n")
            tool_name = None
            tool_args = {}
            
            for line in lines:
                if line.startswith("调用工具:"):
                    tool_name = line.replace("调用工具:", "").strip()
                elif line.startswith("参数:"):
                    args_str = line.replace("参数:", "").strip()
                    try:
                        tool_args = json.loads(args_str)
                    except:
                        tool_args = {"query": args_str}
            
            if tool_name and tool_name in self.tools:
                return {"name": tool_name, "args": tool_args}
        except Exception:
            pass
        
        return None
    
    def _generate_tool_call(self, message: str, history: Optional[List[Dict]] = None, llm = None) -> str:
        if llm is None:
            llm = get_llm()
            
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"""你是一个企业智能客服助手，你的职责是帮助员工解答公司政策、流程规范、产品文档等问题。

你的核心能力包括：
1. 企业知识库检索 - 可以从公司文档中查找相关信息
2. 数据分析 - 可以查询数据库获取业务数据
3. 计算功能 - 可以进行数学计算

可用工具：
{self._build_tool_prompt()}

使用工具的准则：
- 当用户的问题涉及公司政策、产品信息、文档内容时，优先使用知识库检索(rag_retrieve)
- 当用户需要查询业务数据时，使用数据库查询工具(query_database/list_tables/describe_table)
- 当用户需要进行数学计算时，使用计算器工具(calculate)
- 如果不确定答案，应该先检索或查询，而不是猜测
- 如果问题不需要工具，可以直接回答

格式要求：
如果你需要使用工具，请输出：
调用工具: tool_name
参数: {{"query": "查询内容"}}

如果你不需要使用工具，可以直接回答用户的问题。

当前时间：{current_time}"""
        
        messages = [HumanMessage(content=system_prompt)]
        
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        response = llm.invoke(messages)
        return response.content
    
    def chat(self, message: str, history: Optional[List[Dict]] = None) -> str:
        try:
            llm = get_llm()
            tool_response = self._generate_tool_call(message, history, llm)
            
            tool_call = self._parse_tool_call(tool_response)
            
            if tool_call:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if tool_name in self.tools:
                    result = self.tools[tool_name]["function"](**tool_args)
                    
                    final_prompt = f"""根据以下工具执行结果，用自然、友好的语言总结回答用户的问题。

工具执行结果：
{result}

用户问题：
{message}

请提供一个详细的总结回答。"""
                    
                    final_response = llm.invoke([HumanMessage(content=final_prompt)])
                    return final_response.content
                else:
                    return f"未知工具: {tool_name}"
            
            return tool_response
        except ValueError:
            raise
        except Exception as e:
            return f"处理请求时发生错误: {str(e)}"
    
    def stream_chat(self, message: str, history: Optional[List[Dict]] = None):
        llm = get_llm()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        system_prompt = f"""你是一个企业智能客服助手，你的职责是帮助员工解答公司政策、流程规范、产品文档等问题。

当前时间：{current_time}"""
        
        messages = [HumanMessage(content=system_prompt)]
        
        if history:
            for msg in history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=message))
        
        for chunk in llm.stream(messages):
            yield chunk.content

enterprise_agent = EnterpriseAgent()