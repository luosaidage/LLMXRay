from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API 配置
    PROJECT_NAME: str = "LLM-XRay API Scanner"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 探针超时时间 (秒)
    PROBE_TIMEOUT: float = 60.0
    
    # 风险评级阈值
    RISK_HIGH: float = 40.0
    RISK_MEDIUM: float = 70.0
    RISK_LOW: float = 90.0
    
    # 敏感词库
    SENSITIVE_KEYWORDS: List[str] = [
        "cursor", "claude code", "github copilot", "windsurf", 
        "vsc", "vscode", "programming assistant", "codeium", "aider", "replit",
        "expert programmer", "VS Code", "JetBrains", "VSCode extension",
        "Anthropic's Claude", "OpenAI's GPT" # 某些逆向会把官方人设也带上
    ]
    
    # 模拟已知的不良中转域名黑名单
    KNOWN_BAD_DOMAINS: List[str] = [
        "api.fake-ai.com", "cheap-gpt.xyz", "reverse-copilot.net"
    ]
    
    class Config:
        env_file = ".env"

settings = Settings()
