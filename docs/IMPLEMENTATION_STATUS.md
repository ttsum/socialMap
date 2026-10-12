# 当前实施状态（2026-10-06）

本轮按 `EXECUTION_PLAN.md` 继续完成了真实业务接口和小程序 API 服务层：

## 最新进度（2026-10-06）

- **AI Workflow：已升级**。解析接口增加 `intent-v2`、`uncertainFields` 和模型元数据；推荐接口增加 `rank-v2`、候选/命中数和硬过滤字段。Mock 40 条评测完成；真实 GLM 5 条受控冒烟均因读取超时，未标记为质量通过。
- **微信配置：已读取，点击验收待完成**。`/healthz` 已读到 `wechatConfigured=true`；还需要在微信开发者工具中触发 `wx.login`，确认 `/api/v1/auth/wechat/` 返回 200 并完成 JWT 登录。
- **高德地点服务：代码已接入，真实调用待确认**。已加入高德搜索和地理编码服务端代理，Key 只从 `backend/.env` 读取；需看到真实地点搜索结果后再标记高德调用完成。
- **发布需求：代码已接入**。AI 无匹配时可进入发布页，提交带人数、预算、时间和具体地图位置的待审核需求；不会自动生成可加入活动。
- **交互地图：代码已完成**。地图页已由示意图替换为微信原生真实 `<map>`，支持缩放、拖动、旋转、指南针和活动标记；底图为微信地图，地点搜索使用高德。
- **验证**：后端 pytest 19/19、前端 Node 18/18、Mock 评测 40/40、WXML 10/10、WXSS 11/11 通过。

> 状态记录规则：代码完成、隔离测试通过，与真实微信/智谱联调通过分别记录；真实 GLM 请求超时时只记录为外部服务阻塞。详细步骤见 [REAL_INTEGRATION.md](REAL_INTEGRATION.md)。

- Django + DRF 已提供 JWT 微信登录、刷新与退出撤销；微信身份只由服务端 `code2Session` 校验建立。
- 已提供拼团加入/退出、收藏、成员权限校验、聊天消息幂等写入，以及个人拼团、收藏和会话列表接口。
- 小程序 `api` 模式已接入登录令牌、详情页加入/退出/收藏、聊天、消息页和个人页；默认 `local-demo` 保持演示模式隔离。
- 真实 GLM 请求可能接近 30 秒，前端解析请求超时已调整为 40 秒，避免客户端先断开导致后端 `Broken pipe`。
- 后端测试已覆盖登录、权限、重复加入、名额、收藏、消息幂等和非成员拒绝。
- 2026-09-16：本地 `/healthz` 已确认 `aiConfigured=true`、模型为 `glm-5.3`；后端日志出现 `POST /api/v1/ai/parse-intent/ HTTP/1.1 200 416`，证明真实智谱调用和服务端 JSON 解析至少成功一次。此前的 `socket.timeout` 保留为超时故障证据，后续需继续优化超时与重试体验。
- 2026-09-16：已将 `app.js` 默认模式切换为 `api`，执行 `manage.py migrate --noinput`（无待执行迁移）和 `manage.py check` 通过；API 适配器 3/3、前端 smoke 14/14 通过。微信真实登录仍因缺少 `WECHAT_APPSECRET` 未验收。
- 2026-09-16：`GET /healthz` 返回 `aiConfigured=true`、`wechatConfigured=true`、`database=ok`；密钥配置已被后端读取。真实微信登录还需在开发者工具中触发 `wx.login` 并观察 `/api/v1/auth/wechat/` 成功响应，尚未把点击验收标记为完成。
- 2026-09-16：修复智谱请求 `socket.timeout` 未捕获导致 Django 返回 HTML 调试页的问题；超时现在返回可处理的 API 错误，前端过滤 HTML 错误内容。GLM 请求超时配置调整为 40 秒，前端解析请求为 45 秒；后端测试 18/18、API 测试 3/3、smoke 14/14 通过。
- 2026-09-16：开始“找不到后发布需求 + 地图选点”接入：新增 `PublishRequest` 待审核模型和 Admin、`POST/GET /api/v1/publish-requests/`，新增高德地点搜索/地理编码代理，发布页支持地点搜索选择，匹配空状态可进入发布需求流程。当前后端本地数据库迁移因现有服务占用时提示 readonly，测试数据库迁移和代码检查通过；需停止旧服务后重新迁移并配置 `AMAP_API_KEY` 才能完成真实地图调用。
- 2026-09-16：地图页已替换为微信原生真实 `<map>` 组件，启用缩放、拖动、旋转、指南针、活动标记和点击选中；保留 `pins` 兼容字段以维持演示测试。WXML 10/10、WXSS 11/11 编译通过，smoke 14/14 通过。该底图为微信地图，地点搜索仍由高德 API 提供。

## 尚需外部条件

- 真实微信联调需要在后端环境配置 `WECHAT_APPSECRET`。
- 真实智谱调用已配置 `ZHIPU_API_KEY`，模型保持 `glm-5.3`；当前受控请求出现读取超时，需网络可达后复跑完整 40 条评测。
- 微信开发者工具授权超时仍是外部验收阻塞；未据此宣称模拟器点击验收通过。

## 本地运行

```powershell
$env:PATH='D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;' + $env:PATH
cd 团团团\backend
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

开发者工具中将 `app.js` 的 `globalData.mode` 改为 `api`，并把 `apiBaseUrl` 指向本机后端；模拟器访问本机时按工具网络调试规则使用可达地址。
