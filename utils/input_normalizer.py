# utils/input_normalizer.py
"""
用户输入通俗化转换 - 亮点7
将口语化、模糊的输入规整为结构化、清晰的查询
支持意图识别和关键词提取
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
import re
from typing import Dict, List, Optional

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
            temperature=0.1
        )
    return _llm

def normalize_input(user_input: str) -> str:
    """
    将用户输入规整为清晰的研究问题或对话。
    例如：
    "帮我查查最近AI有啥新东西" -> "最近人工智能领域有哪些重要进展？"
    """
    if len(user_input) < 5:
        return user_input
    
    prompt = f"""请将以下用户输入规整为清晰、完整的表达。
如果是提问，请转换为正式的问题形式；如果是闲聊，保持原意但使语句通顺。
只输出转换后的文本，不要有其他解释。

输入：{user_input}
输出："""
    
    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        normalized = response.content.strip()
        if normalized and len(normalized) > 0:
            return normalized
    except:
        pass
    return user_input

def extract_intent(user_input: str) -> str:
    """
    识别用户输入的意图类型。
    返回：research（研究）、chat（闲聊）、command（命令）、question（问题）
    """
    # 规则匹配
    research_keywords = ["研究", "查询", "查一下", "分析", "趋势", "最新", "进展", "报告", "资料", "搜索", "了解", "背景"]
    chat_keywords = ["你好", "嗨", "哈喽", "再见", "谢谢", "天气", "吃饭", "今天", "周末"]
    command_keywords = ["开始", "停止", "重置", "保存", "清除", "帮助"]
    
    input_lower = user_input.lower()
    
    # 规则匹配优先
    if any(kw in input_lower for kw in research_keywords):
        return "research"
    if any(kw in input_lower for kw in chat_keywords):
        return "chat"
    if any(kw in input_lower for kw in command_keywords):
        return "command"
    
    # LLM意图识别
    prompt = f"""分析以下用户输入的意图类型，只返回一个单词：
research - 需要进行研究、搜索、分析的请求
chat - 日常闲聊、问候、情感表达
question - 一般问题，不需要深度研究
command - 系统命令或操作指令

输入：{user_input}
意图："""
    
    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        intent = response.content.strip().lower()
        if intent in ["research", "chat", "question", "command"]:
            return intent
    except:
        pass
    
    # 默认返回question
    return "question"

def extract_keywords(user_input: str, max_keywords: int = 5) -> List[str]:
    """
    从用户输入中提取关键词。
    """
    # 简单规则提取
    keywords = []
    
    # 移除标点符号
    clean_text = re.sub(r'[^\w\s]', '', user_input)
    
    # 常见停用词
    stopwords = ["的", "是", "在", "有", "和", "了", "我", "你", "他", "她", "它", "这", "那", "什么", "怎么", "为什么", "为", "与", "及", "等", "可以", "会", "能", "要", "不", "一个", "一些", "没有", "我们", "你们", "他们", "这个", "那个", "这些", "那些"]
    
    # 提取候选关键词
    words = clean_text.split()
    for word in words:
        if len(word) > 1 and word not in stopwords:
            keywords.append(word)
    
    # LLM提取更准确的关键词
    prompt = f"""从以下文本中提取最多{max_keywords}个核心关键词，用逗号分隔：

文本：{user_input}

关键词："""
    
    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        llm_keywords = [k.strip() for k in response.content.strip().split(',') if k.strip()]
        if llm_keywords:
            return llm_keywords[:max_keywords]
    except:
        pass
    
    return list(set(keywords))[:max_keywords]

def analyze_input(user_input: str) -> Dict:
    """
    综合分析用户输入：标准化、意图识别、关键词提取。
    """
    normalized = normalize_input(user_input)
    intent = extract_intent(user_input)
    keywords = extract_keywords(user_input)
    
    return {
        "original": user_input,
        "normalized": normalized,
        "intent": intent,
        "keywords": keywords,
        "is_research": intent == "research"
    }