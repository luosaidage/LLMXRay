import httpx
from typing import Dict, Any

async def test_temperature_stability(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 7: 温度稳定性测试 (验证是否尊重 temperature=0)"""
    logs = ["Starting temperature stability test (temperature=0)..."]
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "请用一句话描述什么是人工智能。"}],
        "temperature": 0,
        "max_tokens": 100
    }
    
    replies = []
    try:
        for i in range(2):
            logs.append(f"Request {i+1} with temperature=0...")
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            reply = resp.json()['choices'][0]['message']['content'].strip()
            replies.append(reply)
            
        is_stable = replies[0] == replies[1]
        score = 100.0 if is_stable else 30.0
        
        return {
            "module_name": "Temperature Stability Test",
            "passed": is_stable,
            "score": score,
            "evidence": {
                "is_identical": is_stable,
                "reply_1": replies[0][:50] + "...",
                "reply_2": replies[1][:50] + "..."
            },
            "logs": logs + [f"Responses identical: {is_stable}"]
        }
    except Exception as e:
        logs.append(f"Temperature test failed: {str(e)}")
        return {
            "module_name": "Temperature Stability Test",
            "passed": False,
            "score": 0.0,
            "evidence": {"error": str(e)},
            "logs": logs
        }
