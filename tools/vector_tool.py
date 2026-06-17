# tools/vector_tool.py
"""
向量工具 - VectorTool
基于ChromaDB实现语义搜索和文档存储
"""

from tools.base_tool import BaseTool
from utils.vector_store import get_vector_store

class VectorSearchTool(BaseTool):
    """向量检索工具"""
    
    @property
    def name(self) -> str:
        return "vector_search"
    
    @property
    def description(self) -> str:
        return "从知识库中检索相似文档"
    
    def execute(self, params: dict) -> dict:
        query = params.get("query", "")
        n_results = params.get("n_results", 5)
        
        if not query:
            return {"success": False, "error": "查询参数不能为空"}
        
        try:
            vector_store = get_vector_store()
            results = vector_store.search(query, n_results=n_results)
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}

class VectorStoreTool(BaseTool):
    """向量存储工具"""
    
    @property
    def name(self) -> str:
        return "vector_store"
    
    @property
    def description(self) -> str:
        return "将文档存储到向量知识库"
    
    def execute(self, params: dict) -> dict:
        documents = params.get("documents", [])
        metadatas = params.get("metadatas", [])
        
        if not documents:
            return {"success": False, "error": "文档列表不能为空"}
        
        try:
            vector_store = get_vector_store()
            vector_store.add_documents(documents, metadatas)
            return {"success": True, "count": len(documents)}
        except Exception as e:
            return {"success": False, "error": str(e)}