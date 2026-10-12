# 真实微信与智谱联调配置

## 为什么当前没有标记为完成

后端代码和隔离测试已经完成，但真实联调需要访问两个外部服务：

1. 微信 `code2Session`：必须配置小程序对应的 `WECHAT_APPSECRET`。
2. 智谱 GLM：必须配置服务端 `ZHIPU_API_KEY`。

密钥没有写入代码、前端包、日志或版本库，因此在当前环境没有密钥时只能验证 mock 和错误处理，不能声称真实登录或真实模型调用成功。

## 配置方式

在 `backend` 目录创建本地 `.env` 或直接设置当前终端环境变量。不要提交该文件：

推荐本地开发使用 `backend/.env`，项目启动时会自动读取；该文件已加入 `.gitignore`：

```text
WECHAT_APPID=wxcabe02fe45ec7f3c
WECHAT_APPSECRET=你的微信AppSecret
ZHIPU_API_KEY=你的智谱APIKey
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-5.3
```

也可以复制模板后再编辑：

```powershell
Copy-Item .env.example .env
```

```powershell
$env:WECHAT_APPID='wxcabe02fe45ec7f3c'
$env:WECHAT_APPSECRET='微信公众平台/小程序后台获取的 AppSecret'
$env:ZHIPU_API_KEY='智谱开放平台生成的 API Key'
$env:ZHIPU_BASE_URL='https://open.bigmodel.cn/api/paas/v4'
$env:LLM_MODEL='glm-5.3'
```

启动后端：

```powershell
$env:PATH='D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;' + $env:PATH
cd 团团团\backend
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

如果 Windows 报错 `ImportError: DLL load failed while importing _sqlite3`，直接运行项目内脚本，它会自动补充 Anaconda SQLite DLL 路径：

```powershell
cd 团团团\backend
powershell -ExecutionPolicy Bypass -File .\run-local.ps1
```

## 联调顺序

1. 先请求 `GET /healthz`，确认数据库可用并检查 AI 配置状态。
2. 在微信开发者工具中将 `app.js` 的 `globalData.mode` 改为 `api`，`apiBaseUrl` 指向后端可达地址。
3. 通过小程序触发登录，确认 `POST /api/v1/auth/wechat/` 返回访问令牌。
4. 使用登录后的账号测试活动详情、加入/退出、收藏和聊天。
5. 在发布页提交中文需求，确认 `POST /api/v1/ai/parse-intent/` 使用 `glm-5.3` 返回并通过服务端结构校验。

## 标记规则

- 只有真实微信 code 登录成功、数据库写入成功，并完成至少一次 GLM 真实解析后，才能把真实联调标记为完成。
- 任一密钥缺失、模型不可用、微信 code 无效或开发者工具未完成授权，都保持“代码完成，真实联调待验证”。
