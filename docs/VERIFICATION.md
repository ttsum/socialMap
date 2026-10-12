# 项目验收与证据记录

## 当前验收结论

截至 2026-10-06，源码级和自动化验收已完成：前端本地演示闭环、后端首期接口、API 适配、AI Workflow、Mock 评测以及 WXML/WXSS 编译均通过。当前不能宣称产品已完成整体验收，因为微信开发者工具实际渲染/点击、PostgreSQL Compose、真实 GLM 成功响应、真机和生产环境仍没有完整证据。

未完成项按依赖分为：

- 外部授权：微信开发者工具 Codex 客户端授权连接超时，导致模拟器点击、控制台和截图无法执行。
- 本机服务：Docker Desktop 未安装，PostgreSQL Compose 尚未启动；API 适配代码已测，但微信工具中的 `api` 模式尚未端到端运行。
- 外部服务：后端 `.env` 已配置 `ZHIPU_API_KEY`；2026-10-06 对真实 GLM 做了 5 条受控冒烟，其中 1 条成功、4 条读取超时，完整质量评测暂不下结论。
- 产品后续阶段：微信登录、真实加入/退出、群组权限、实时聊天、支付、定位/地图 SDK、RAG、行为反馈和 HTTPS 上线均未实现。

## 已通过

- Node 测试 14 项（脚本：tests/smoke.test.js）。
- 原生 wcc 编译全部 10 个页面/组件模板。
- 原生 wcsc 编译全部 11 个页面/组件/全局样式。
- 核心状态变化、异常条件与页面方法调用链测试。
- 配置保留原 AppID，并将设计、文档和验证文件排除在小程序包外。
- 2026-09-15 23:22 +08:00 再次执行 `node --test tests/smoke.test.js`：14 项通过、0 失败。
- 2026-09-15 23:22 +08:00 使用官方 `wcc.exe` / `wcsc.exe` 再次编译：10 个 WXML、11 个 WXSS 全部通过。
  - 微信开发者工具占用 `.qa` 时，使用 `--output "$env:TEMP\tuantuantuan-compiler-20260915-2320"` 隔离本轮产物；不影响小程序包与既有 `.qa` 证据。
- 2026-09-15 静态响应式审查：检查全局、9 个页面与活动卡组件的弹性收缩、长文本换行、聊天滚动/安全区和键盘位置调整声明；未发现可由源码确定的关键遮挡或滚动失效问题。
- 静态审查后已将通用卡片、空状态与活动卡主体圆角收至 `16rpx`，并将标题字距设为 `0`；需在模拟器的 375 / 390 / 430 逻辑宽度下作实际渲染确认。
- 上述样式修正后再次执行 `node --test tests/smoke.test.js`：14 项通过、0 失败；官方 `wcc.exe` / `wcsc.exe`：WXML 10/10、WXSS 11/11 通过。独立编译产物位于 `%TEMP%\tuantuantuan-compiler-20260915-static-audit`。
- 2026-09-15 环境复核：确认 `D:\ProgramData\Anaconda3\python.exe` 为 Python 3.9.12；项目专用 `backend\.venv` 依赖导入成功。
- 2026-09-15 最终代码复验：`node --test tests/api.test.js` 为 3/3；Django `manage.py check` 通过，原生测试为 13/13。执行 Django 命令时需把 Anaconda 的 `Library\bin` 和根目录加入当前 `PATH`，用于加载 Windows SQLite DLL。
- 2026-09-15 官方编译器复验：WXML 10/10、WXSS 11/11 通过，产物位于 `%TEMP%\tuantuantuan-compiler-20260915-final`。

测试产物位于 .qa/，不进入小程序包。

## 不能由上述测试证明的事项

- 页面在微信模拟器的实际渲染与点击。
- 无运行期 WXML/JS 错误。
- 原生组件、键盘、滚动、分享及真机兼容性。
- 视觉与原型一致性。

## 模拟器连接记录

本机安装版本：2.02.2608070。安装诊断兼容。
客户端：Codex。入口：wechatide.cmd。
检查登录/版本时触发首次客户端授权，连接以以下错误结束：

```
CONNECT_ERROR
wait WechatIDE authorization timeout
source: auth
tool: check_wechatide_status
```

未返回 taskId；不再自动重复授权请求。
用户已决定暂缓授权；不再自动重试连接。开发者工具连接可用后，继续模拟器验收。

2026-09-15 23:19 +08:00 再次检查时，`check_wechatide_status` 自动请求授权后仍在 30 秒内超时，返回同一错误：

```text
CONNECT_ERROR
wait WechatIDE authorization timeout
source: auth
tool: check_wechatide_status
```

因此本轮没有模拟器运行页面、控制台、点击或截图证据；以下手动验收项仍全部待办。

## 模拟器手动验收清单

- [ ] 首页 6 条活动显示正常，所有 Tab 可切换。
- [ ] 地图分类与点位点击能更新选中的活动。
- [ ] 输入默认需求后显示 4 人、周六下午、5 公里、100 元。
- [ ] 修改确认条件影响结果；无结果时可返回修改。
- [ ] 加入活动按人数占位，取消弹窗不占位，重复加入不重复占位。
- [ ] 收藏与已加入在我的页正确显示。
- [ ] 消息页显示已加入的会话，发送内容后返回仍保留。
- [ ] 退出拼团后消息列表消失、名额恢复，旧聊天入口不允许发送。
- [ ] 游客、未加入、错误 ID 和空结果有明确提示。
- [ ] 键盘打开时输入和发送按钮可见，聊天自动滚到最新消息。
- [ ] 不同手机宽度下无文字截断、遮挡或底部导航覆盖。
- [ ] 控制台无业务 JS/WXML/WXSS 运行错误。

## 后端与 API 联调证据

- 2026-09-15：Django 原生测试 13 项通过，覆盖活动列表/分类、详情成员规则、非法 ID、推荐硬过滤、空结果、过期活动、非法参数、健康检查和 Provider JSON/Schema/fallback。
- 2026-09-15：小程序 API 适配器测试 3 项通过，覆盖 API 模式开关、列表/推荐成功解包、HTTP/网络错误和重试所需错误文案。
- 2026-09-15：`D:\ProgramData\Anaconda3\python.exe` 为 Python 3.9.12；`backend/.venv` 依赖导入成功；Django `manage.py check` 通过。
- Django 测试数据库迁移并调用 `seed_demo` 成功，导入 6 条活动、6 个拼团和 4 个成员；PostgreSQL Compose 尚未运行。
- 本机尚未安装 Docker Desktop；后端已配置 `ZHIPU_API_KEY`，但 2026-10-06 的 5 条真实 GLM 冒烟请求中 4 条读取超时。API 模式不会把请求失败静默降级为 mock。

## 2026-10-06 AI 产品闭环验证

- `node --test tests/smoke.test.js tests/api.test.js`：18/18 通过。
- `python -m pytest backend -q -p no:cacheprovider`：19 passed，6 个依赖库 JWT 密钥长度警告。
- `node scripts/check-templates.js ...`：WXML 10/10、WXSS 11/11 通过；产物写入 `%TEMP%\tuantuantuan-compiler-20261006-ai`。
- Mock 评测：40/40；核心字段宏平均准确率 1.0000；偏好 F1 0.9630；不确定字段召回率 1.0000；硬过滤违规 0；事实解释违规 0。
- 真实 GLM 受控冒烟：5 条中 1 条成功、4 条在约 9.3 秒后返回 `The read operation timed out`；报告位于 `.qa/ai-eval-glm-smoke.json`，状态为 `blocked_or_partial`，该结果不作为模型质量评分。
- Mock 报告位于 `.qa/ai-eval-mock.json`；完整 GLM 40 条评测命令已实现，待外部服务可达后运行。
