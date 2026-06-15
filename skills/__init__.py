# skills/__init__.py
from skills.base_skill import Skill
from skills.web_search_skill import WebSearchSkill
from skills.web_fetch_skill import WebFetchSkill
from skills.report_gen_skill import ReportGenSkill
from skills.vector_search_skill import VectorSearchSkill, VectorStoreSkill

_skills = {
    "web_search": WebSearchSkill(),
    "web_fetch": WebFetchSkill(),
    "report_gen": ReportGenSkill(),
    "vector_search": VectorSearchSkill(),
    "vector_store": VectorStoreSkill(),
}

def get_skill(name: str) -> Skill:
    return _skills.get(name)

def register_skill(name: str, skill: Skill):
    _skills[name] = skill