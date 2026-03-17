from schemas.models import ScanReport
from typing import Any
import json

def generate_html_report(report: ScanReport) -> str:
    """生成可视化的 HTML 报告"""
    
    # 颜色映射
    risk_colors = {
        "Safe": "#10b981", # Green
        "Low": "#3b82f6",  # Blue
        "Medium": "#f59e0b", # Orange
        "High": "#ef4444"   # Red
    }
    
    risk_color = risk_colors.get(report.risk_level, "#6b7280")
    
    # 模块说明映射
    module_descriptions = {
        "Prompt Leak Test": "提示词泄露与劫持检测。通过注入攻击指令，检测模型是否容易被诱导泄露其内部系统提示词或被恶意劫持。",
        "Token Math Audit": "Token 计费审计。检测是否存在严重的 Token 虚标、滥用或截断现象，保护用户的计费权益。",
        "API Feature Test": "原生 API 高级特性测试 (FC, JSON)。验证模型对复杂指令的理解和结构化输出能力，是区分高级模型的重要指标。",
        "Model Identity Consistency": "身份一致性检测。验证模型是否如实申报其身份，防止模型“张冠李戴”（例如用 GPT-3.5 冒充 GPT-4）。",
        "Stream Stability & Latency": "响应稳定性测试。在多次并发请求下，检测模型输出的连贯性与一致性，评估中转链路的稳定性。",
        "Concurrency & Rate Limit": "并发与速率限制测试。检测 API 在高并发下的表现，评估后端中转服务的承载能力。",
        "Temperature Precision": "采样温度敏感度测试。验证模型是否真实遵循 API 的温度参数设置，检测后端是否存在固定输出或缓存行为。"
    }
    
    details_html = ""
    chart_labels = []
    chart_scores = []
    
    for detail in report.details:
        status_color = "#10b981" if detail.passed else "#ef4444"
        status_text = "PASSED" if detail.passed else "FAILED"
        description = module_descriptions.get(detail.module_name, "该模块负责对 API 的特定功能进行深度探测与评估。")
        
        evidence_json = json.dumps(detail.evidence, indent=2, ensure_ascii=False)
        
        chart_labels.append(detail.module_name)
        chart_scores.append(detail.score)
        
        details_html += f"""
        <div class="module-card">
            <div class="module-header">
                <span class="module-name">{detail.module_name}</span>
                <span class="module-status" style="background-color: {status_color}">{status_text} ({detail.score:.1f} pts)</span>
            </div>
            <div class="module-description">{description}</div>
            <div class="module-evidence">
                <pre>{evidence_json}</pre>
            </div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LLM-XRay 体检报告 - {report.target_model}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #f3f4f6;
                color: #1f2937;
                line-height: 1.5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                color: #111827;
                margin: 0;
            }}
            .subtitle {{
                color: #6b7280;
                margin-top: 8px;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                margin-bottom: 30px;
            }}
            .summary-item {{
                text-align: center;
                padding: 15px;
                background: #f9fafb;
                border-radius: 8px;
            }}
            .summary-label {{
                font-size: 12px;
                color: #6b7280;
                text-transform: uppercase;
                display: block;
                margin-bottom: 5px;
            }}
            .summary-value {{
                font-size: 20px;
                font-weight: bold;
            }}
            .risk-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 9999px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
            .chart-container {{
                margin-bottom: 40px;
                padding: 20px;
                background: #f9fafb;
                border-radius: 12px;
                height: 400px;
            }}
            .module-card {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-bottom: 20px;
                overflow: hidden;
            }}
            .module-header {{
                background: #f9fafb;
                padding: 12px 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #e5e7eb;
            }}
            .module-name {{
                font-weight: bold;
                font-size: 16px;
            }}
            .module-status {{
                font-size: 12px;
                padding: 2px 8px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }}
            .module-description {{
                padding: 15px 20px 0;
                font-size: 14px;
                color: #4b5563;
                line-height: 1.6;
            }}
            .module-evidence {{
                padding: 15px 20px;
                background: white;
            }}
            pre {{
                background: #f1f5f9;
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #9ca3af;
                font-size: 12px;
            }}
            .hijack-alert {{
                background-color: #fef2f2;
                border: 1px solid #fee2e2;
                color: #991b1b;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">LLM-XRay API 体检报告</h1>
                <p class="subtitle">生成时间: {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            {f'<div class="hijack-alert">⚠️ 警告：该接口疑似存在劫持或预设污染风险！</div>' if report.is_hijacked else ''}

            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-label">目标模型</span>
                    <span class="summary-value">{report.target_model}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">综合评分</span>
                    <span class="summary-value" style="color: {risk_color}">{report.total_score:.1f}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">风险等级</span>
                    <span class="summary-value">
                        <span class="risk-badge" style="background-color: {risk_color}">{report.risk_level}</span>
                    </span>
                </div>
            </div>

            <div class="chart-container">
                <canvas id="scoreChart"></canvas>
            </div>

            <div class="details-section">
                <h2 style="font-size: 18px; margin-bottom: 15px;">详细探测项说明</h2>
                {details_html}
            </div>

            <div class="footer">
                <p>LLM-XRay (API 照妖镜) - 保护您的 AI 资产安全</p>
                <p>报告 ID: {report.task_id}</p>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('scoreChart').getContext('2d');
            new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: {json.dumps(chart_labels, ensure_ascii=False)},
                    datasets: [{{
                        label: '得分情况',
                        data: {json.dumps(chart_scores)},
                        backgroundColor: '{risk_color}33',
                        borderColor: '{risk_color}',
                        borderWidth: 2,
                        pointBackgroundColor: '{risk_color}',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '{risk_color}'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        r: {{
                            angleLines: {{
                                display: true
                            }},
                            suggestedMin: 0,
                            suggestedMax: 100,
                            ticks: {{
                                stepSize: 20
                            }}
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_template
