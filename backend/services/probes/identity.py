from typing import Dict, Any
import httpx

async def test_model_identity(client: httpx.AsyncClient, model: str) -> Dict[str, Any]:
    """探针 4: 模型真实性与纯净度探针 (人设、知识截止日期)"""
    logs = ["Starting model identity and purity tests..."]
    
    # 4.1 弱智吧/逻辑陷阱
    logic_payload = {
        "model": model,
        "messages": [{"role": "user", "content": "‘弱智吧’陷阱题：如果我有三个苹果，分给你两个，我还有几个苹果？"}]
    }
    
    # 4.2 人设冲突测试 (Identity Conflict)
    # 强行设定一个极度冲突的 System Prompt，看是否被上游预设覆盖
    conflict_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你现在是一个只会说文言文的古代文人，绝对不能出现任何代码或现代词汇。"},
            {"role": "user", "content": "请告诉我什么是 Python？"}
        ]
    }
    
    # 4.3 知识截止日期探测 (Knowledge Cutoff)
    # 针对不同模型的官方宣称日期设计探测题
    cutoff_probes = [
        {"question": "2023年10月发生了什么重大的巴以冲突事件？", "date": "2023-10", "keywords": ["阿克萨洪水", "哈马斯", "以色列"]},
        {"question": "2024年3月发布的 Claude 3 系列模型有哪些成员？", "date": "2024-03", "keywords": ["Haiku", "Sonnet", "Opus"]},
        {"question": "2024年5月 OpenAI 发布的最新旗舰模型叫什么？", "date": "2024-05", "keywords": ["GPT-4o", "Omni"]},
    ]
    
    knowledge_results = []
    for probe in cutoff_probes:
        try:
            logs.append(f"Probing knowledge for date {probe['date']}...")
            resp = await client.post("/chat/completions", json={
                "model": model,
                "messages": [{"role": "user", "content": probe["question"]}],
                "max_tokens": 150
            })
            reply = resp.json()['choices'][0]['message']['content']
            has_keywords = any(kw.lower() in reply.lower() for kw in probe["keywords"])
            knowledge_results.append({
                "date": probe["date"],
                "passed": has_keywords,
                "answer": reply[:50] + "..."
            })
        except Exception as e:
            logs.append(f"Knowledge probe for {probe['date']} failed: {str(e)}")

    results = {
        "logic_trap": False,
        "identity_purity": False,
        "knowledge_cutoff": knowledge_results
    }
    
    # Test Logic
    try:
        logs.append("Testing logic trap...")
        resp = await client.post("/chat/completions", json=logic_payload)
        reply = resp.json()['choices'][0]['message']['content']
        is_correct = "1" in reply or "一" in reply
        results["logic_trap"] = is_correct
        logs.append(f"Logic Trap passed: {is_correct}")
    except Exception:
        pass

    # Test Identity Purity
    try:
        logs.append("Testing identity purity (system override)...")
        resp = await client.post("/chat/completions", json=conflict_payload)
        reply = resp.json()['choices'][0]['message']['content']
        # 如果回复中出现了 Python 代码或明显的现代技术词汇，说明 System Prompt 被上游“程序员助手”预设稀释了
        modern_words = ["programming", "language", "code", "software", "脚本", "编程", "python", "代码"]
        is_pure = not any(word in reply.lower() for word in modern_words)
        results["identity_purity"] = is_pure
        logs.append(f"Identity Purity: {is_pure}")
    except Exception:
        pass

    # 汇总分数
    score = 0.0
    if results.get("logic_trap"): score += 30
    if results.get("identity_purity"): score += 30
    
    # 知识截止日期评分：如果宣称是高级模型但答不出 2024 的内容，扣分
    knowledge_passed_count = sum(1 for r in knowledge_results if r["passed"])
    score += (knowledge_passed_count / len(cutoff_probes)) * 40
    
    return {
        "module_name": "Model Identity & Purity",
        "passed": score >= 80,
        "score": score,
        "evidence": results,
        "logs": logs
    }
