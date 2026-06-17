# utils/skill_parser.py
"""
技能文档解析器 - 将Markdown格式的技能文档转换为AI可理解的格式

特点：
1. 支持Markdown格式的技能定义文档
2. 提取技能名称、描述、适用场景、参数、执行步骤、输出格式
3. 将技能信息格式化为LLM可理解的文本
4. 支持动态加载多个技能文档
"""

import os
import re
from typing import Dict, Any, List, Optional

class SkillDocument:
    """技能文档对象 - 存储解析后的技能信息"""
    
    def __init__(self, name: str, description: str, scenarios: List[str],
                 parameters: List[Dict[str, str]], steps: List[str],
                 output_format: str, examples: str):
        self.name = name              # 技能名称
        self.description = description  # 技能描述
        self.scenarios = scenarios      # 适用场景列表
        self.parameters = parameters    # 参数定义列表
        self.steps = steps              # 执行步骤列表
        self.output_format = output_format  # 输出格式示例
        self.examples = examples        # 使用示例
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "scenarios": self.scenarios,
            "parameters": self.parameters,
            "steps": self.steps,
            "output_format": self.output_format,
            "examples": self.examples
        }

class SkillParser:
    """技能文档解析器 - 加载和解析Markdown格式的技能文档"""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skill_docs: Dict[str, SkillDocument] = {}
        self._load_all_skills()
    
    def _load_all_skills(self):
        """加载目录中所有技能文档"""
        if not os.path.exists(self.skills_dir):
            print(f"⚠️ 技能目录不存在: {self.skills_dir}")
            return
        
        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".skill.md"):
                skill_name = filename.replace(".skill.md", "")
                filepath = os.path.join(self.skills_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        doc = self._parse_markdown(content)
                        doc.name = skill_name
                        self.skill_docs[skill_name] = doc
                        print(f"✅ 加载技能文档: {skill_name}")
                except Exception as e:
                    print(f"❌ 加载技能文档失败 {filename}: {e}")
    
    def _parse_markdown(self, content: str) -> SkillDocument:
        """解析Markdown格式的技能文档"""
        # 提取描述
        desc_match = re.search(r'## 描述\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # 提取适用场景
        scenarios = []
        scenarios_match = re.search(r'## 适用场景\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if scenarios_match:
            for line in scenarios_match.group(1).strip().split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    scenarios.append(line[2:])
        
        # 提取输入参数（表格格式）
        parameters = []
        params_match = re.search(r'## 输入参数\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if params_match:
            lines = params_match.group(1).strip().split("\n")
            header_found = False
            for line in lines:
                if line.startswith("|") and "参数名" in line:
                    header_found = True
                    continue
                if header_found and line.startswith("|"):
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    if len(parts) >= 3:
                        parameters.append({
                            "name": parts[0],
                            "type": parts[1],
                            "description": parts[2]
                        })
        
        # 提取执行步骤
        steps = []
        steps_match = re.search(r'## 执行步骤\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if steps_match:
            for line in steps_match.group(1).strip().split("\n"):
                line = line.strip()
                match = re.match(r'^(\d+)\.\s*(.+)$', line)
                if match:
                    steps.append(match.group(2))
        
        # 提取输出格式（JSON代码块）
        output_format = ""
        output_match = re.search(r'## 输出格式\s*\n```json\s*([\s\S]*?)```', content)
        if output_match:
            output_format = output_match.group(1).strip()
        
        # 提取使用示例
        examples = ""
        examples_match = re.search(r'## 使用示例\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
        if examples_match:
            examples = examples_match.group(1).strip()
        
        return SkillDocument(
            name="",
            description=description,
            scenarios=scenarios,
            parameters=parameters,
            steps=steps,
            output_format=output_format,
            examples=examples
        )
    
    def get_skill_doc(self, name: str) -> Optional[SkillDocument]:
        """根据名称获取技能文档"""
        return self.skill_docs.get(name)
    
    def list_skills(self) -> List[str]:
        """列出所有可用技能名称"""
        return list(self.skill_docs.keys())
    
    def format_for_llm(self, include_examples: bool = False) -> str:
        """
        将技能文档格式化为LLM可理解的文本
        
        Args:
            include_examples: 是否包含使用示例（会增加Token消耗）
        
        Returns:
            格式化后的技能文档文本
        """
        if not self.skill_docs:
            return "暂无可用技能"
        
        result = "=== 可用技能列表 ===\n\n"
        for name, doc in self.skill_docs.items():
            result += f"【技能名称】{name}\n"
            result += f"【描述】{doc.description}\n"
            result += f"【适用场景】{', '.join(doc.scenarios)}\n"
            result += f"【参数】{', '.join([p['name'] + ':' + p['type'] for p in doc.parameters])}\n"
            
            if include_examples and doc.examples:
                result += f"【使用示例】\n{doc.examples}\n"
            
            result += "---\n\n"
        
        return result
    
    def get_decision_prompt(self, user_question: str, current_step: str = "") -> str:
        """
        生成技能选择决策提示词
        
        Args:
            user_question: 用户问题
            current_step: 当前步骤（可选）
        
        Returns:
            完整的决策提示词
        """
        skills_text = self.format_for_llm(include_examples=False)
        
        # 根据步骤类型添加提示
        step_hint = ""
        if "搜索" in current_step:
            step_hint = "提示：当前是'搜索'步骤，应该使用 web_search 技能"
        elif "阅读" in current_step:
            step_hint = "提示：当前是'阅读'步骤，应该使用 web_fetch 技能（需要URL参数）"
        elif "报告" in current_step or "生成" in current_step:
            step_hint = "提示：当前是'报告'步骤，应该使用 report_gen 技能"
        elif "整理" in current_step or "总结" in current_step:
            step_hint = "提示：当前是'整理'步骤，不需要使用技能，请返回 no_skill"
        
        prompt = f"""
你是一个智能技能调用决策助手。请根据用户问题和当前步骤判断是否需要使用技能，并选择最合适的技能。

=== 用户信息 ===
用户问题：{user_question}
当前步骤：{current_step or '无'}

=== 可用技能 ===
{skills_text}

{step_hint}

=== 决策要求 ===
1. 根据当前步骤类型选择最合适的技能
2. 严格按照步骤提示选择技能
3. 确定调用参数
4. 给出明确的决策理由

=== 输出格式 ===
请严格按照以下JSON格式输出：
{{
    "decision": "use_skill" 或 "no_skill",
    "skill_name": "技能名称"（如果decision为use_skill）,
    "parameters": {{"参数名": "值"}}（如果decision为use_skill）,
    "reason": "决策理由"
}}
"""
        return prompt

# 全局技能解析器实例
_skill_parser = None

def get_skill_parser() -> SkillParser:
    """获取全局技能解析器实例"""
    global _skill_parser
    if _skill_parser is None:
        _skill_parser = SkillParser()
    return _skill_parser

def load_skill_docs() -> None:
    """重新加载所有技能文档"""
    global _skill_parser