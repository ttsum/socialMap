# 团团团前端结构与接入说明

## 本轮边界

当前交付包含可独立运行的本地演示前端，以及可选的 Django + DRF 本机 API 首期：活动检索、活动详情、服务端推荐和 GLM 意图解析。真实微信登录、真实加入/退出、支付、实时聊天、地图 SDK 和生产上线仍不在本期范围。

## 页面与导航

| 页面 | 路由 | 导航方式 |
|---|---|---|
| 首页 | pages/index/index | Tab |
| 地图示意 | pages/map/map | Tab |
| 发布需求 | pages/publish/publish | Tab |
| 消息列表 | pages/messages/messages | Tab |
| 我的 | pages/profile/profile | Tab |
| 条件确认 | pages/confirm/confirm | navigateTo |
| 匹配结果 | pages/matches/matches | navigateTo |
| 拼团详情 | pages/detail/detail?id=活动ID | navigateTo |
| 群聊 | pages/chat/chat?groupId=拼团ID | navigateTo |

匹配页进入详情时额外携带 `people` 和 `source=matches`；直接浏览活动默认 1 人。
返回修改条件采用 redirectTo，避免确认页和匹配页重复堆栈。

## 数据关系

- `activities.id`：活动 ID。
- `groups.activityId`：关联活动；`groups.id` 贯穿加入、会话和消息。
- `groups.memberIds`：关联示例成员。
- 当前演示每个活动对应一个拼团；真实系统可扩展为一个活动多个团。
- `store.list()` 合并活动、成员数量、本机加入人数、收藏状态，供各页统一使用。
- 页面 `onShow` 重新读取状态；返回或切换 Tab 后更新名额、收藏和会话。
- 加入时校验身份、活动状态和名额；重复加入不重复占位；退出释放我方全部名额。
- 本地状态不会跨设备同步，也不支持多个真实用户；名额一致性只在单机演示范围内成立。

## 需求与推荐

`data/mock-ai.js` 输出：
`query / people / day / period / maxDistanceKm / budgetPerPerson / preferences / city / notes`。

- 人数包含本人；“和三位朋友”为 4 人。
- 日期范围只包含下一次演示周末的周六、周日和不限；具体日期及时刻提示手动确认。
- 复杂否定与比较表达可能无法可靠解析，必须人工核对。
- 城市固定为长沙。
- 偏好为软条件，只影响排序；预算、距离、时段和容量为硬条件。
- 当前距离为活动示例字段；没有真实定位或路线距离计算。
- 推荐理由使用实际返回的活动字段；无匹配时显示空状态，不偷偷放宽条件。

## 后端首期

- `backend/activities` 保存活动、拼团和成员模型，保留前端现有活动/拼团/成员 ID。
- `GET /api/v1/activities/` 支持 `category` 筛选；详情返回活动、规则、成员和名额。
- `POST /api/v1/ai/parse-intent/` 由服务端调用智谱兼容接口并校验 JSON；默认 `glm-5.3`，仅模型明确不可用时尝试一次 `glm-5.2`。
- `POST /api/v1/recommendations/` 在服务端执行城市、时间、容量、预算、距离硬过滤和确定性排序；价格、距离、名额和理由不由模型生成。
- `GET /healthz` 返回服务、数据库和 AI 配置状态，不返回密钥或用户原始需求。
- `services/api.js` 只在 `app.js` 的 `globalData.mode === 'api'` 时调用后端。列表、地图、匹配和详情请求失败显示错误与重试；演示身份、收藏、加入、退出、消息和聊天仍使用本机存储。

完整字段约定见 [API_CONTRACT.md](API_CONTRACT.md)。

## 接入状态与后续替换顺序

已完成：

1. 新建 `services/api.js`，保留 `local-demo`，API 模式错误明确展示，不把演示加入伪装成真实报名成功。
2. 首页、地图、发布解析、匹配和详情已改为可选异步 service，并具备加载、失败和重试状态。
3. 活动查询保留现有活动 ID / 拼团 ID，并统一日期时间、金额单位、坐标和 camelCase 响应字段。
4. GLM 返回结构化 JSON 后由服务端执行 schema 校验；推荐由服务端根据活动事实过滤、排序并生成理由。

后续替换顺序：

1. 真实加入接口由服务端事务保证容量、重复请求和成员权限，客户端检查只能改善提示。
2. 登录由服务端交换微信 code，身份由服务端验证；不直接以本机 `loggedIn` 布尔值作为权限依据。
3. 聊天接口验证成员资格，支持分页、去重及发送失败重试；之后再增加 WebSocket。
4. 接地图 SDK 时替换示意图，补定位许可、拒绝定位路径与基于真实坐标的距离计算。
5. 增加行为事件、推荐评测和活动资料检索，再考虑 RAG / 活动问答。

本机 API 首期已实现并完成 SQLite 内存库测试；PostgreSQL 由 `backend/docker-compose.yml` 提供。Docker Desktop 尚未在本机安装，因此 Compose 联调和真实 GLM 调用仍待环境条件满足。

## 验证范围

- Node 测试：结构、解析、硬过滤、容量、身份取消、状态持久化、整条页面方法调用链、缺失 ID、空结果。
- 原生 wcc / wcsc：项目全部模板和样式的编译。
- 仍需模拟器与真机检验：真实点击、长屏滚动、键盘避让、中文布局、底部安全区、运行控制台和分享路径。
- 后端测试：Django 原生测试 13 项通过；受限工作区中 pytest 在全通过后的退出阶段挂起，暂以原生命令作为稳定证据。

## AI 产品闭环与评测

- 解析接口由 `intent-v2` Prompt 生成结构化条件，并返回模型、Prompt 版本、耗时和 fallback 元数据。
- `uncertainFields` 标记复杂日期、否定、比较或缺失条件；用户在确认页手动核对后才进入推荐。
- 推荐接口由 `rank-v2` 执行事实字段硬过滤和确定性排序，并返回候选数、命中数和过滤字段。
- 40 条样本由 `evaluate_ai` 分别执行 Mock 回归和真实 GLM 对照；报告只保存样本 ID、指标和错误类型。
- 真实 GLM 评测受 `ZHIPU_API_KEY` 和网络可达性影响；请求失败不会静默降级为 Mock。
