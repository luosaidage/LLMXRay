from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from schemas.models import ScanRequest, TaskResponse, ScanReport, WSMessage
from services.scanner_engine import ScannerEngine, tasks_db
from services.report_generator import generate_html_report
import uuid
import asyncio
from typing import Dict
from datetime import datetime

router = APIRouter(prefix="/api/v1/scans", tags=["API Scanner"])

# 存储活跃的 WebSocket 连接和对应的任务 ID
active_engines: Dict[str, ScannerEngine] = {}

@router.post("/", response_model=TaskResponse)
async def create_scan_task(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    提交 API 体检任务 (异步)
    """
    task_id = str(uuid.uuid4())
    # 初始化任务状态
    tasks_db[task_id] = {
        "status": "pending",
        "progress": 0,
        "report": None,
        "request": request
    }
    
    # 初始化引擎并存储
    engine = ScannerEngine(task_id, request)
    active_engines[task_id] = engine
    
    # 异步运行体检
    background_tasks.add_task(engine.run_all_tests)
    
    return TaskResponse(
        task_id=task_id,
        status="processing",
        message="API 体检任务已成功启动"
    )

@router.get("/{task_id}/status")
async def get_task_status(task_id: str):
    """
    获取任务实时状态 (轮询接口)
    """
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task_id,
        "status": tasks_db[task_id]["status"],
        "progress": tasks_db[task_id].get("progress", 0)
    }

@router.get("/{task_id}/report", response_model=ScanReport)
async def get_scan_report(task_id: str):
    """
    获取完整的体检报告
    """
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_data = tasks_db[task_id]
    if task_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="体检报告尚未准备就绪")
      
    return task_data["report"]

@router.get("/{task_id}/report/html", response_class=HTMLResponse)
async def get_html_report(task_id: str):
    """
    获取可视化的 HTML 体检报告
    """
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task_data = tasks_db[task_id]
    if task_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="体检报告尚未准备就绪")
      
    report = task_data["report"]
    html_content = generate_html_report(report)
    return html_content

@router.websocket("/ws/{task_id}")
async def websocket_scan_progress(websocket: WebSocket, task_id: str):
    """
    WebSocket: 实时推送体检日志和进度
    """
    await websocket.accept()
    
    # 如果任务还没启动，可能任务已经完成或者 task_id 无效
    if task_id not in active_engines:
        # 如果已经有报告，直接发完成消息
        if task_id in tasks_db and tasks_db[task_id]["status"] == "completed":
            await websocket.send_json(WSMessage(type="complete", data=tasks_db[task_id]["report"].model_dump()).model_dump())
            await websocket.close()
            return
        else:
            await websocket.send_json(WSMessage(type="error", message="任务不存在或已过期").model_dump())
            await websocket.close()
            return

    engine = active_engines[task_id]
    
    try:
        # 持续从日志队列中读取并推送
        while True:
            try:
                # 设置超时以检查任务状态
                log_msg = await asyncio.wait_for(engine.log_queue.get(), timeout=1.0)
                
                if log_msg == "DONE":
                    # 确保报告已生成
                    report = tasks_db[task_id].get("report")
                    if report:
                        # 转换 datetime 为字符串，避免 JSON 序列化错误
                        report_dict = report.model_dump()
                        if isinstance(report_dict.get('created_at'), datetime):
                            report_dict['created_at'] = report_dict['created_at'].isoformat()
                        
                        await websocket.send_json(WSMessage(type="complete", data=report_dict).model_dump())
                    else:
                        await websocket.send_json(WSMessage(type="error", message="报告生成失败").model_dump())
                    break
                elif log_msg.startswith("ERROR:"):
                    await websocket.send_json(WSMessage(type="error", message=log_msg).model_dump())
                    break
                else:
                    await websocket.send_json(WSMessage(
                        type="log", 
                        message=log_msg,
                        data={"progress": tasks_db[task_id].get("progress", 0)}
                    ).model_dump())
            except asyncio.TimeoutError:
                # 检查任务是否已经结束（例如在连接 WebSocket 前就结束了）
                if tasks_db[task_id]["status"] in ["completed", "failed"]:
                    break
                continue
    except WebSocketDisconnect:
        print(f"Client disconnected for task {task_id}")
    finally:
        # 任务结束，清理引擎引用
        if task_id in active_engines:
            del active_engines[task_id]
