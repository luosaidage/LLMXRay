from typing import Dict, Any
import httpx

async def test_token_audit(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 2: Token 消耗精确审计 (防止注入与注水)"""
    # 发送一段大概 500 个单词的文本，通常 1 个单词 ~ 1.3 tokens
    # 我们构造一个可预测 token 数的文本
    test_word = "hello "
    word_count = 400
    exact_text = test_word * word_count
    
    # 估算期望的 prompt_tokens (基于常见的 GPT/Claude tokenizer)
    # "hello " 在大部分 tokenizer 中是 1 个 token
    expected_tokens_min = 380
    expected_tokens_max = 450
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": exact_text}],
        "max_tokens": 10,
        "temperature": 0.0
    }
    
    logs = [f"Sending token audit request with {word_count} words..."]
    try:
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
      
        usage = data.get('usage', {})
        billed_prompt_tokens = usage.get('prompt_tokens', 0)
        logs.append(f"API reported prompt_tokens: {billed_prompt_tokens}")
        
        # 判定逻辑：
        # 如果 billed_prompt_tokens 显著大于 word_count，说明有隐藏注入
        # 如果差距超过 200 tokens，基本可以实锤有长系统提示词
        diff = billed_prompt_tokens - word_count
        
        is_suspicious = diff > 200 
        
        # 动态打分
        if diff <= 50:
            score = 100.0
        elif diff <= 200:
            score = 80.0
        else:
            # 差距越大分数越低，每多 100 token 扣 20 分
            score = max(0, 60.0 - (diff - 200) / 5)
            
        return {
            "module_name": "Token Math Audit",
            "passed": not is_suspicious,
            "score": score,
            "evidence": {
                "expected_tokens": f"~{word_count}", 
                "billed_tokens": billed_prompt_tokens,
                "token_overhead": diff,
                "usage_raw": usage
            },
            "logs": logs
        }
    except Exception as e:
        logs.append(f"Error during token audit test: {str(e)}")
        return {
            "module_name": "Token Math Audit",
            "passed": False,
            "score": 0.0,
            "evidence": {"error": str(e)},
            "logs": logs
        }
