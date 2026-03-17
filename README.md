# LLM-XRay (API 照妖镜)

**LLM-XRay** 是一款专注于大模型中转 API 真伪与纯净度检测的工具。它通过多维度的探针（Probes）技术，识别中转 API 是否存在“系统提示词污染”、“逆向劫持”、“偷取 Token”或“模型挂羊头卖狗肉”等现象。

---

## 🚀 项目实现

以下是当前功能的实现进度对照表：

### 1. 核心检测逻辑 (Core Detection Logic)

| 功能模块                        | 描述                                                 | 实现状态 | 相关代码                                                                                       |
| :------------------------------ | :--------------------------------------------------- | :-------: | :--------------------------------------------------------------------------------------------- |
| **系统提示词泄露测试**    | 诱导模型吐出原始 System Prompt，检测隐藏注入         | ✅ 已实现 | [prompt_leak.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/prompt_leak.py) |
| **Token 消耗校验**        | 通过精确 Token 计算识别隐藏预设或注水计费            | ✅ 已实现 | [token_audit.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/token_audit.py) |
| **Function Calling 测试** | 验证接口是否支持标准的工具调用功能                   | ✅ 已实现 | [func_call.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/func_call.py)     |
| **JSON Mode 测试**        | 验证 `response_format: {type: 'json_object'}` 支持 | ✅ 已实现 | [func_call.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/func_call.py)     |
| **人设冲突测试**          | 强行设定冲突身份，检测上游预设的“权重污染”         | ✅ 已实现 | [identity.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/identity.py)       |
| **温度稳定性测试**        | 验证模型是否真实遵循采样温度参数，检测后端缓存行为   | ✅ 已实现 | [temperature.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/temperature.py) |
| **弱智吧/逻辑陷阱测试**   | 通过经典难题识别模型底层能力（打假小模型伪装）       | ✅ 已实现 | [identity.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/identity.py)       |
| **流式输出稳定性测试**    | 分析 Chunk 间隔与大小，识别套壳网页版爬虫            | ✅ 已实现 | [stability.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/stability.py)     |
| **高并发压力测试**        | 检测账号池轮询及 429 报错频率                        | ✅ 已实现 | [stability.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/probes/stability.py)     |
| **多模态 (Vision) 测试**  | 验证图片 Base64 传输与分析能力                       | ❌ 待实现 | -                                                                                              |

### 2. 软件功能模块 (Software Features)

| 功能模块                  | 详细功能                                                    | 实现状态 | 备注                                                                                              |
| :------------------------ | :---------------------------------------------------------- | :-------: | :------------------------------------------------------------------------------------------------ |
| **一键体检**        | 输入 URL/Key 自动运行全量探针                               | ✅ 已实现 | [scanner_engine.py](file:///c:/Users/sai/Codex\plan/LLM-XRay/backend/services/scanner_engine.py)     |
| **cURL 解析**       | 前端支持粘贴 cURL 命令自动提取参数                          | ✅ 已实现 | [index.html](file:///c:/Users/sai/Codex/plan/LLM-XRay/frontend/index.html)                           |
| **实时日志推送**    | 通过 WebSocket 展示后端探测过程                             | ✅ 已实现 | [routes.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/api/routes.py)                          |
| **综合评分体系**    | 0-100 分纯净度评分与风险等级判定                            | ✅ 已实现 | [scanner_engine.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/scanner_engine.py)     |
| **可视化报告**      | 生成带有**雷达图** 和 **模块说明** 的 HTML 报告 | ✅ 已实现 | [report_generator.py](file:///c:/Users/sai/Codex/plan/LLM-XRay/backend/services/report_generator.py) |
| **多地区延迟追踪**  | 分析 API 真实节点位置                                       | ❌ 待实现 | 需要多节点代理支持                                                                                |
| **IP 隔离测试**     | 连续请求检测是否分配到不同逆向账号                          | ❌ 待实现 | 需要会话 ID 追踪逻辑                                                                              |
| **报告分享/黑名单** | 生成分享链接及建立避雷社区                                  | ❌ 待实现 | 需要数据库持久化支持                                                                              |

---

## 🛠️ 技术栈

- **后端 (Backend)**: FastAPI + Python 3.12+uv
- **异步处理**: `asyncio` + `httpx` (并发探测)
- **实时通信**: `WebSocket` (日志流)
- **前端 (Frontend)**: Tailwind CSS + Vanilla JS + **Chart.js** (可视化展示)

---

## 🏃 快速启动

### 1. 安装依赖

```bash
uv add -r requirements.txt
```

### 2. 运行后端服务

```bash
# 方式一：直接运行后端脚本 (默认Loaclhost，端口 10001)
uv run backend/main.py

# 方式二：使用 uvicorn 运行
uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 10001 --reload
```

### 3. 访问前端

访问 `http://127.0.0.1:10001` 即可进入检测首页。

---

## 📝 待办清单 (Roadmap)

- [ ] 增加 **Vision (多模态)** 探测模块。
- [ ] 完善 **知识截止日期 (Knowledge Cutoff)** 的精准对比库。
- [ ] 实现 **IP 漂移检测**，识别多账号池轮询。
- [ ] 增加 **IP 隔离测试**，识别逆向多账号。
- [ ] 开发 **报告分享** 功能。
