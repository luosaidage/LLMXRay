import asyncio
import time
from typing import Dict, Any
import httpx
import json

async def test_stream_stability(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 5: 流式输出稳定性与延迟测试 (识别套壳网页版)"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Write a long story about a robot (at least 200 words)."}],
        "stream": True,
        "max_tokens": 300
    }
    
    logs = ["Starting stream stability test..."]
    chunks = []
    start_time = time.time()
    first_token_time = None
    
    try:
        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                
                if first_token_time is None:
                    first_token_time = time.time() - start_time
                
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                
                try:
                    chunk_data = json.loads(data_str)
                    if not chunk_data.get('choices'): continue
                    content = chunk_data['choices'][0]['delta'].get('content', '')
                    if content:
                        chunks.append({
                            "content": content,
                            "timestamp": time.time() - start_time
                        })
                except Exception:
                    continue

        end_time = time.time()
        total_duration = end_time - start_time
        
        # 分析流的稳定性
        intervals = []
        for i in range(1, len(chunks)):
            intervals.append(chunks[i]['timestamp'] - chunks[i-1]['timestamp'])
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        stutters = [i for i in intervals if i > 0.5] 
        avg_chunk_len = sum(len(c['content']) for c in chunks) / len(chunks) if chunks else 0
        
        is_suspicious = avg_chunk_len > 15 or len(stutters) > 5
        
        score = 100.0
        if avg_chunk_len > 10: score -= 30
        if len(stutters) > 3: score -= 20
        if first_token_time and first_token_time > 2.0: score -= 20
        
        return {
            "module_name": "Stream Stability & Latency",
            "passed": not is_suspicious,
            "score": max(0, score),
            "evidence": {
                "first_token_latency": f"{first_token_time:.2f}s" if first_token_time else "N/A",
                "avg_chunk_interval": f"{avg_interval*1000:.1f}ms",
                "avg_chunk_length": f"{avg_chunk_len:.1f} chars",
                "stutter_count": len(stutters),
                "total_duration": f"{total_duration:.2f}s"
            },
            "logs": logs + [f"First token: {first_token_time:.2f}s", f"Avg chunk len: {avg_chunk_len:.1f}"]
        }
    except Exception as e:
        logs.append(f"Stream test failed: {str(e)}")
        return {
            "module_name": "Stream Stability & Latency",
            "passed": False,
            "score": 0.0,
            "evidence": {"error": str(e)},
            "logs": logs
        }

async def test_concurrency(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 6: 高并发压力测试 (识别账号池轮询)"""
    concurrency_count = 5 
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi, just say 'ok'."}],
        "max_tokens": 5
    }
    
    logs = [f"Starting concurrency test with {concurrency_count} simultaneous requests..."]
    
    async def single_request():
        try:
            start = time.time()
            resp = await client.post("/chat/completions", json=payload)
            duration = time.time() - start
            return {"status": resp.status_code, "latency": duration}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    tasks = [single_request() for _ in range(concurrency_count)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r.get("status") == 200)
    avg_latency = sum(r.get("latency", 0) for r in results if r.get("status") == 200) / (success_count or 1)
    
    is_stable = success_count == concurrency_count
    score = (success_count / concurrency_count) * 100
    
    return {
        "module_name": "Concurrency Pressure Test",
        "passed": is_stable,
        "score": score,
        "evidence": {
            "success_rate": f"{success_count}/{concurrency_count}",
            "avg_latency": f"{avg_latency:.2f}s",
            "results_raw": results
        },
        "logs": logs + [f"Success rate: {success_count}/{concurrency_count}"]
    }
