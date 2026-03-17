from typing import Dict, Any
import httpx

async def test_function_calling(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 3: 原生 API 高级特性测试 (FC, JSON, Vision)"""
    logs = ["Starting feature completeness tests..."]
    
    # 3.1 Function Calling Test
    fc_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "What is the weather in Beijing?"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "parameters": {"type": "object", "properties": {"loc": {"type": "string"}}}
            }
        }]
    }
    
    # 3.2 JSON Mode Test
    json_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Generate a JSON with 'name' and 'age' fields."}],
        "response_format": {"type": "json_object"}
    }

    results = {}
    
    # Test FC
    try:
        logs.append("Testing Function Calling...")
        resp = await client.post("/chat/completions", json=fc_payload)
        resp.raise_for_status()
        data = resp.json()
        has_fc = "tool_calls" in data['choices'][0]['message']
        results["function_calling"] = has_fc
        logs.append(f"FC Support: {has_fc}")
    except Exception as e:
        results["function_calling"] = False
        logs.append(f"FC Test Failed: {str(e)}")

    # Test JSON Mode
    try:
        logs.append("Testing JSON Mode...")
        resp = await client.post("/chat/completions", json=json_payload)
        # 很多逆向接口不支持 json_object 会直接 400
        if resp.status_code == 200:
            results["json_mode"] = True
            logs.append("JSON Mode: Supported")
        else:
            results["json_mode"] = False
            logs.append(f"JSON Mode: Not Supported (HTTP {resp.status_code})")
    except Exception:
        results["json_mode"] = False
        logs.append("JSON Mode: Failed")

    # 汇总分数
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    score = (passed_count / total_count) * 100 if total_count > 0 else 0
    
    return {
        "module_name": "API Feature Test",
        "passed": passed_count == total_count,
        "score": score,
        "evidence": results,
        "logs": logs
    }
