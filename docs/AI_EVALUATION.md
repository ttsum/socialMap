# AI 评测说明

## 运行方式

在项目目录执行：

```powershell
$env:PATH='D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;'+$env:PATH
$env:DATABASE_URL='sqlite:///:memory:'
backend\.venv\Scripts\python.exe backend\manage.py evaluate_ai `
  --dataset data\ai_eval_cases.json `
  --provider mock `
  --output .qa\ai-eval-mock.json
```

真实模型使用：

```powershell
backend\.venv\Scripts\python.exe backend\manage.py evaluate_ai `
  --dataset data\ai_eval_cases.json `
  --provider glm `
  --output .qa\ai-eval-glm.json
```

受控冒烟可使用 `--limit 5`，并通过 `LLM_TIMEOUT_SECONDS` 设置单请求超时。

## 评测集

`data/ai_eval_cases.json` 包含 40 条人工构造样本，覆盖完整需求、中文数字、缺失条件、日期/时间表达、否定/比较表达、非法参数和边界条件。报告只保存样本 ID、预测字段和错误类型，不重复保存原始需求文本。

## 指标与门槛

- 核心字段宏平均准确率：目标 ≥ 0.95。
- 偏好识别 F1：目标 ≥ 0.85。
- 不确定字段召回率：目标 ≥ 0.80。
- 硬过滤违规数：目标 0。
- 推荐理由事实违规数：目标 0。
- 报告记录平均、P50、P95 和最大响应耗时。

Mock Provider 用于稳定回归；GLM Provider 用于真实模型对照。真实请求失败时，指标只代表“请求不可用”，不能解读为模型准确率。

## 当前结果

2026-10-06：

- Mock：40/40 完成；核心字段宏平均准确率 1.0000；偏好 F1 0.9630；不确定字段召回率 1.0000；硬过滤违规 0；事实解释违规 0。
- GLM 受控冒烟：5 条请求中 1 条成功、4 条因 `The read operation timed out` 失败；平均耗时约 9.3 秒。报告状态为 `blocked_or_partial`，样本量不足且存在外部服务阻塞，不作为模型质量评分。
