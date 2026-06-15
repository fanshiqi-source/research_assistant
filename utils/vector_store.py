# utils/vector_store.py
"""
文本检索与向量化处理 - 亮点13
使用ChromaDB和sentence-transformers实现语义检索
"""

import os
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any

DATA_DIR = os.environ.get("DATA_ROOT", "D:/generated_outputs/research_assistant")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db")

class VectorStore:
    def __init__(self, collection_name: str = "research_knowledge"):
        os.makedirs(CHROMA_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        # 使用sentence-transformers嵌入模型
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """添加文档到向量库"""
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadatas is None:
            metadatas = [{}] * len(documents)
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
    
    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """语义检索最相关的文档"""
        results = self.collection.query(query_texts=[query], n_results=n_results)
        output = []
        if results['documents']:
            for doc, meta, dist in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                output.append({
                    "content": doc,
                    "metadata": meta,
                    "score": 1 - dist  # 距离转相似度
                })
        return output
    
    def search_with_context(self, query: str, context_prefix: str = "") -> str:
        """检索并格式化为上下文文本"""
        results = self.search(query)
        if not results:
            return ""
        context = context_prefix + "\n"
        for i, r in enumerate(results, 1):
            context += f"[{i}] {r['content'][:500]}\n"
        return context

# 全局实例
_vector_store = None
def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store