# skills/web_fetch_skill.py
import requests
from bs4 import BeautifulSoup
from skills.base_skill import Skill

class WebFetchSkill(Skill):
    @property
    def name(self) -> str:
        return "web_fetch"
    
    @property
    def description(self) -> str:
        return "抓取指定URL的网页正文内容"
    
    def execute(self, params: dict) -> dict:
        url = params.get("url", "")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.encoding = resp.apparent_encoding or resp.encoding
            soup = BeautifulSoup(resp.text, 'html.parser')
            for s in soup(["script", "style"]):
                s.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            truncated = text[:3000] + "..." if len(text) > 3000 else text
            return {"success": True, "content": truncated, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e), "content": ""}