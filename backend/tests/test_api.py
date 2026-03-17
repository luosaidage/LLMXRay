import pytest
from fastapi.testclient import TestClient
from main import app
from services.scanner_engine import tasks_db
import uuid
from datetime import datetime

client = TestClient(app)

def test_root():
    """测试根路径是否正常"""
    response = client.get("/")
    assert response.status_code == 200
    assert "LLM-XRay" in response.text or response.json()["project"] == "LLM-XRay"

def test_create_scan_task():
    """测试创建体检任务"""
    payload = {
        "api_url": "https://api.openai.com/v1",
        "api_key": "sk-test-key",
        "target_model": "gpt-4o"
    }
    response = client.post("/api/v1/scans/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"
    
    task_id = data["task_id"]
    assert task_id in tasks_db

def test_get_task_status():
    """测试获取任务状态"""
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "status": "processing",
        "progress": 50,
        "report": None
    }
    
    response = client.get(f"/api/v1/scans/{task_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 50

def test_get_report_not_ready():
    """测试在任务未完成时获取报告"""
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {
        "status": "processing",
        "progress": 50,
        "report": None
    }
    
    response = client.get(f"/api/v1/scans/{task_id}/report")
    assert response.status_code == 400
    assert "尚未准备就绪" in response.json()["detail"]

def test_get_html_report():
    """测试获取 HTML 报告"""
    task_id = str(uuid.uuid4())
    # 模拟一个完整的报告数据
    mock_report = {
        "task_id": task_id,
        "target_model": "gpt-4o",
        "total_score": 95.5,
        "risk_level": "Safe",
        "is_hijacked": False,
        "details": [
            {
                "module_name": "Prompt Leak Test",
                "passed": True,
                "score": 100.0,
                "evidence": {"found": "none"},
                "logs": ["Test log"]
            }
        ],
        "created_at": datetime.now()
    }
    
    from schemas.models import ScanReport
    report_obj = ScanReport(**mock_report)
    
    tasks_db[task_id] = {
        "status": "completed",
        "progress": 100,
        "report": report_obj
    }
    
    response = client.get(f"/api/v1/scans/{task_id}/report/html")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "LLM-XRay 体检报告" in response.text
    assert "gpt-4o" in response.text
    assert "95.5" in response.text

def test_invalid_task_id():
    """测试无效的任务 ID"""
    response = client.get("/api/v1/scans/invalid-id/status")
    assert response.status_code == 404
