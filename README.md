# 团团团 · AI-LBS 拼团推荐小程序

原生微信小程序前端演示版，以长沙的线下活动为场景，支持：
**描述需求 → 修改解析条件 → 匹配活动 → 加入拼团 → 群聊 → 我的管理**。

## 运行

1. 在微信开发者工具中导入本目录。
2. 保留已配置的 AppID：`wxcabe02fe45ec7f3c`。须由具有该项目权限的微信账号打开。
3. 点击普通编译，首页为 `pages/index/index`。
4. 当前 `app.js` 默认使用本机 `api` 模式；若只想离线演示，将 `globalData.mode` 改为 `local-demo`，无需后端、AI 密钥或网络接口。

### 本机 API 模式

后端依赖已安装到 `backend/.venv`，Python 版本为 3.9.12。启动本机 Django API：

```powershell
cd backend
$env:PATH='D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;'+$env:PATH
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py seed_demo
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

`backend\.venv` 使用 `D:\ProgramData\Anaconda3\python.exe` 创建。Windows 上保留上面的 PATH 设置，否则 Python 可能找不到 Anaconda 自带的 SQLite `_sqlite3` DLL。

默认开发配置使用 SQLite；Docker Compose 启动时使用 PostgreSQL。若要让小程序请求本机 API，在 `app.js` 将 `globalData.mode` 改为 `api`，并在开发者工具中允许本地调试请求。API 路径和响应字段见 [docs/API_CONTRACT.md](docs/API_CONTRACT.md)。

智谱密钥只放在后端环境变量 `ZHIPU_API_KEY`，不要写入小程序代码、`app.js` 或聊天记录。

首页、地图、发布、消息、我的为五个 Tab；确认、匹配、详情、群聊为流程页，共 9 个页面。

## 一次完整演示

1. 首页点击需求入口，选择第一条示例：
   “周六下午和三位朋友，找长沙市区五公里内、人均100元以内、安静一点的活动”。
2. 点击“让 AI 帮我找”；确认同行总人数为 4，并可修改时间、距离、预算和偏好。
3. 开始匹配，进入“橘子洲日落慢走”等活动详情。
4. 加入时选择“使用演示身份”，再确认加入；进入群聊发送一条消息。
5. 切换消息页查看会话，在我的页查看已加入的拼团。
6. 在详情页收藏或退出拼团，检查首页、地图、消息和我的同步变化。

## 当前能力与边界

- 6 条示例活动、6 个拼团、4 个示例成员；活动排期随启动日期安排到周末。
- 本地规则提取常见人数、时间段、预算、距离和偏好；确认页支持手动修改。
- 推荐执行城市、日期、时段、人数名额、距离和预算硬过滤，偏好参与排序。
- 地图为基于示例坐标绘制的位置示意，不是导航地图；距离不是实时定位。
- 发布用于寻找已有拼团；暂不支持用户创建新活动或新拼团。
- 演示身份不调用真实微信登录；不提供真实报名、支付或多人实时通信。
- 收藏、加入人数、需求草稿和聊天记录保存于 `wx` 本地存储，键为 `tuantuantuan.demo.v1`。
- 退出身份保留记录；清理开发者工具存储会清除演示记录。
- AI 推荐分仅为排序指标，不代表匹配概率。未知日期、复杂否定等自然语言须手动核对。

## 目录

| 路径 | 用途 |
|---|---|
| `pages/` | 9 个页面 |
| `components/activity-card/` | 统一的活动卡片 |
| `data/` | 示例活动、拼团、成员、消息和规则解析 |
| `services/store.js` | 数据查询、推荐、演示身份、收藏、加入和聊天 |
| `services/api.js` | 本机 API 请求封装；只在 `api` 模式启用 |
| `utils/navigation.js` | Tab / 流程页跳转封装 |
| `assets/icons/` | 原创底部导航图标 |
| `prototypes/` | 原有设计参考，保留原文件 |
| `scripts/` | 原生模板编译检查、图标生成 |
| `tests/` | 无额外依赖的 Node 测试 |
| `docs/` | 目标、开发路线、执行状态和接入说明 |

原型图与文档、测试脚本、验证产物已列入小程序打包忽略项。

## 验证

安装 Node.js 后，在本目录运行：

```powershell
node --test tests/smoke.test.js
node --test tests/api.test.js
node scripts/check-templates.js 'D:\LeStoreDownload\微信web开发者工具\resources\app.asar.unpacked\node_modules\wcc-exec'
```

第二条命令需替换成本机含 `wcc.exe` 和 `wcsc.exe` 的目录，结果写入 `.qa/compiler-report.json`。
若微信开发者工具占用 `.qa`，可传入隔离输出目录，例如：

```powershell
node scripts/check-templates.js 'D:\LeStoreDownload\微信web开发者工具\resources\app.asar.unpacked\node_modules\wcc-exec' --output "$env:TEMP\tuantuantuan-compiler"
```

它只验证 WXML/WXSS 编译，不等同于模拟器整包运行或真机验收。

重新生成底部图标：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/generate-tab-icons.ps1
```

后端测试（Windows 需要先加入 Anaconda 的 SQLite DLL 路径）：

```powershell
$env:PATH='D:\ProgramData\Anaconda3\Library\bin;D:\ProgramData\Anaconda3;'+$env:PATH
$env:DATABASE_URL='sqlite:///:memory:'
backend\.venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider
```

AI 评测会自动迁移内存数据库并导入 6 条示例活动：

```powershell
backend\.venv\Scripts\python.exe backend\manage.py evaluate_ai --dataset data\ai_eval_cases.json --provider mock --output .qa\ai-eval-mock.json
backend\.venv\Scripts\python.exe backend\manage.py evaluate_ai --dataset data\ai_eval_cases.json --provider glm --output .qa\ai-eval-glm.json
```

真实 GLM 评测从后端环境变量 `ZHIPU_API_KEY` 读取密钥；网络不稳定时可加 `--limit 5` 做受控冒烟，并用 `LLM_TIMEOUT_SECONDS` 设置单请求超时。评测报告不保存原始需求文本或密钥。

## 后续开发

- 当前状态与验收记录：[docs/EXECUTION_PLAN.md](docs/EXECUTION_PLAN.md)
- 后端接入与数据说明：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 宏观路线：[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)
- 原始长期目标：[docs/GOAL.md](docs/GOAL.md)
