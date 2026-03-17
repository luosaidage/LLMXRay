from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime

# 1. 提交检测请求
class ScanRequest(BaseModel):
    api_url: HttpUrl = Field(..., description="要检测的中转 API Base URL")
    api_key: str = Field(..., description="测试用的 API Key")
    target_model: str = Field(..., example="gpt-4o", description="号称的模型名称")
    # 可选：用户想跑哪些测试？(默认全跑)
    test_modules: List[str] = Field(
        default=["prompt_leak", "token_audit", "feature_test", "model_identity"],
        description="选择要执行的体检模块"
    )

# 2. 基础响应格式
class TaskResponse(BaseModel):
    task_id: str
    status: str = Field(..., example="processing|completed|failed")
    message: str

# 3. 详细的评测报告项
class TestResultDetail(BaseModel):
    module_name: str
    passed: bool
    score: float = Field(default=0.0, description="单项得分 0-100")
    evidence: Optional[Dict[str, Any]] = Field(None, description="实锤证据，如泄露的预设、Token差异图")
    logs: List[str] = Field(default=[], description="测试过程日志")

# 4. 完整的体检报告
class ScanReport(BaseModel):
    task_id: str
    target_model: str
    total_score: float = Field(..., description="API 纯净度总分")
    risk_level: str = Field(..., example="High|Medium|Low|Safe", description="风险评级")
    is_hijacked: bool = Field(..., description="是否被判定为套壳/劫持")
    details: List[TestResultDetail]
    created_at: datetime = Field(default_factory=datetime.now)

# 5. WebSocket 消息格式
class WSMessage(BaseModel):
    type: str = Field(..., example="log|progress|complete|error")
    message: Optional[str] = None
    data: Optional[Any] = None
