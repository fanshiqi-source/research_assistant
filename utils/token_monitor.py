# utils/token_monitor.py
"""
Token流量监控 + 单轮消耗监管 - 亮点12
统计每次调用的token数，支持阈值告警
"""

import tiktoken
from typing import Optional

class TokenMonitor:
    def __init__(self, model: str = "gpt-4o-mini", warn_threshold: int = 4000):
        self.model = model
        self.warn_threshold = warn_threshold
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的token数"""
        return len(self.encoder.encode(text))
    
    def estimate_tokens(self, *texts: str) -> int:
        """估算多个文本的总token数"""
        total = 0
        for text in texts:
            total += self.count_tokens(text)
        return total
    
    def check_threshold(self, tokens: int) -> Optional[str]:
        """检查是否超过阈值，返回警告信息"""
        if tokens > self.warn_threshold:
            return f"⚠️ Token用量超阈值：{tokens} > {self.warn_threshold}"
        return None
    
    def log_usage(self, session_id: str, input_text: str, output_text: str):
        """记录单次对话的token消耗"""
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total = input_tokens + output_tokens
        warning = self.check_threshold(total)
        # 实际应用中可写入数据库
        print(f"[TokenMonitor] session={session_id}, in={input_tokens}, out={output_tokens}, total={total}")
        if warning:
            print(warning)
        return {"input": input_tokens, "output": output_tokens, "total": total, "warning": warning}