import asyncio
import httpx
from typing import Dict, Any, List
from datetime import datetime
from loguru import logger

from schemas.models import ScanRequest, ScanReport, TestResultDetail
from core.config import settings
from services.probes.prompt_leak import test_prompt_leak
from services.probes.token_audit import test_token_audit
from services.probes.func_call import test_function_calling
from services.probes.identity import test_model_identity
from services.probes.stability import test_stream_stability, test_concurrency
from services.probes.temperature import test_temperature_stability

# 全局内存数据库 (生产环境请用 Redis)
tasks_db: Dict[str, Dict[str, Any]] = {}

class ScannerEngine:
    def __init__(self, task_id: str, request: ScanRequest):
        self.task_id = task_id
        self.request = request
        self.client = httpx.AsyncClient(
            base_url=str(self.request.api_url),
            headers={"Authorization": f"Bearer {self.request.api_key}"},
            timeout=settings.PROBE_TIMEOUT
        )
        # 日志回调列表，用于推送给 WebSocket
        self.log_queue: asyncio.Queue = asyncio.Queue()

    async def _log(self, message: str):
        logger.info(f"[{self.task_id}] {message}")
        await self.log_queue.put(message)

    async def run_all_tests(self):
        """执行所有体检项目并汇总结果"""
        try:
            tasks_db[self.task_id]["status"] = "processing"
            tasks_db[self.task_id]["progress"] = 0
            
            # 0. 黑名单预检查 (Blacklist Check)
            is_blacklisted = any(domain in str(self.request.api_url) for domain in settings.KNOWN_BAD_DOMAINS)
            if is_blacklisted:
                await self._log("WARNING: API Domain found in known bad/hijack blacklist!")
            
            await self._log(f"Starting scan task for model: {self.request.target_model}")
            
            # 1. 准备任务列表
            probe_tasks = []
            if "prompt_leak" in self.request.test_modules:
                probe_tasks.append(test_prompt_leak(self.client, self.request.target_model))
            if "token_audit" in self.request.test_modules:
                probe_tasks.append(test_token_audit(self.client, self.request.target_model))
            if "feature_test" in self.request.test_modules:
                probe_tasks.append(test_function_calling(self.client, self.request.target_model))
            if "model_identity" in self.request.test_modules:
                probe_tasks.append(test_model_identity(self.client, self.request.target_model))
            
            # 默认全跑稳定性与温度测试 (如果没在 modules 里指定，我们也跑)
            probe_tasks.append(test_stream_stability(self.client, self.request.target_model))
            probe_tasks.append(test_concurrency(self.client, self.request.target_model))
            probe_tasks.append(test_temperature_stability(self.client, self.request.target_model))
            
            await self._log(f"Initialized {len(probe_tasks)} probes. Running concurrently...")
            tasks_db[self.task_id]["progress"] = 20
            
            # 2. 并发执行探针
            results = await asyncio.gather(*probe_tasks, return_exceptions=True)
            
            await self._log("All probes completed. Processing results...")
            tasks_db[self.task_id]["progress"] = 80
            
            # 3. 汇总报告
            test_details = []
            total_score = 0.0
            is_hijacked = False
            
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Probe failed with exception: {str(res)}")
                    continue
                
                detail = TestResultDetail(**res)
                test_details.append(detail)
                total_score += detail.score
                
                # 劫持判定逻辑
                # 1. Prompt Leak 没过
                # 2. Token 审计分数极低
                # 3. 稳定性测试发现网页版特征
                if detail.module_name == "Prompt Leak Test" and not detail.passed:
                    is_hijacked = True
                if detail.module_name == "Token Math Audit" and detail.score < 40:
                    is_hijacked = True
                if detail.module_name == "Stream Stability & Latency" and not detail.passed:
                    # 流式稳定性不一定代表劫持，但如果分数极低也是风险
                    pass
            
            # 计算平均分
            final_score = total_score / len(test_details) if test_details else 0.0
            
            # 判定风险等级
            risk_level = "Safe"
            if is_hijacked or final_score < settings.RISK_HIGH:
                risk_level = "High"
            elif final_score < settings.RISK_MEDIUM:
                risk_level = "Medium"
            elif final_score < settings.RISK_LOW:
                risk_level = "Low"
            
            report = ScanReport(
                task_id=self.task_id,
                target_model=self.request.target_model,
                total_score=final_score,
                risk_level=risk_level,
                is_hijacked=is_hijacked or is_blacklisted, # 黑名单直接判定劫持
                details=test_details,
                created_at=datetime.now()
            )
            
            # 4. 更新任务状态
            tasks_db[self.task_id]["status"] = "completed"
            tasks_db[self.task_id]["progress"] = 100
            tasks_db[self.task_id]["report"] = report
            
            await self._log(f"Scan task completed. Final Score: {final_score:.2f}, Risk Level: {risk_level}")
            await self.log_queue.put("DONE") # 发送结束标志
            
        except Exception as e:
            logger.exception(f"Unexpected error in scanner engine: {str(e)}")
            tasks_db[self.task_id]["status"] = "failed"
            tasks_db[self.task_id]["message"] = str(e)
            await self.log_queue.put(f"ERROR: {str(e)}")
        finally:
            await self.client.aclose()
