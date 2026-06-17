# skills/__init__.py
"""
Skill 技能文档注册中心
管理所有技能文档（.skill.md），用于 LLM 阅读后决策
"""

from tools import get_tool, list_tools

# 提供统一接口（兼容旧代码）
def get_skill(name: str):
    """获取工具实例"""
    return get_tool(name)

def list_skills():
    """列出所有可用技能"""
    return list_tools()

def register_skill(name: str, skill):
    """注册新技能（兼容旧代码）"""
    from tools import register_tool
    register_tool(name, skill)