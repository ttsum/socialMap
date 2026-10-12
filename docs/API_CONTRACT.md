# 本机 API 契约

基础地址：`http://127.0.0.1:8000`

小程序默认使用 `local-demo`。开发者工具联调时，将 `app.js` 中的 `globalData.mode` 改为 `api`；`apiBaseUrl` 默认是 `http://127.0.0.1:8000/api/v1`。开发者工具需要允许本地调试请求。生产 HTTPS、合法域名和证书不在本期完成。

## `GET /api/v1/activities/`

可选查询参数：`category`，例如 `户外`。返回：

```json
{
  "items": [
    {
      "id": "a-walk",
      "groupId": "g-walk",
      "title": "橘子洲日落慢走",
      "category": "户外",
      "locationName": "橘子洲",
      "address": "长沙市岳麓区橘子洲景区入口",
      "city": "长沙",
      "lat": 28.185,
      "lng": 112.96,
      "distanceKm": 2.4,
      "pricePerPerson": 0,
      "priceLabel": "免费",
      "capacity": 8,
      "joinedCount": 3,
      "joinedSeats": 0,
      "remaining": 5,
      "startTime": "2026-09-19T16:00:00+08:00",
      "dateLabel": "09/19 周六 16:00",
      "durationHours": 2,
      "tags": ["安静", "散步"],
      "theme": "mint",
      "symbol": "洲",
      "description": "沿江慢慢走。",
      "meetingPoint": "景区入口游客指示牌旁"
    }
  ]
}
```

## `GET /api/v1/activities/{id}/`

返回 `{ "activity": Activity, "group": Group }`。`Group` 包含 `id`、`hostUserId`、`status`、`rules` 和 `members`；成员包含 `id`、`name`、`initial`、`color`。

## `POST /api/v1/ai/parse-intent/`

请求体：`{ "query": "周六下午和三位朋友，找长沙市区五公里内、人均100元以内的安静活动" }`，最多 300 字。

成功返回 `{ "intent": Intent, "meta": ParseMeta }`。`Intent` 使用前端 camelCase 字段：`query`、`people`、`day`、`period`、`maxDistanceKm`、`budgetPerPerson`、`preferences`、`city`、`notes`、`uncertainFields`。`ParseMeta` 包含 `model`、`promptVersion`、`latencyMs`、`fallbackUsed`。后端会校验字段、范围和枚举；AI 异常不会静默改用本地规则。

`uncertainFields` 用于标记需要用户确认的字段，例如复杂日期、否定表达或缺失预算；小程序确认页在用户确认前不会进入推荐。

## `POST /api/v1/recommendations/`

请求体为已确认的 `Intent` 条件。返回 `{ "items": Activity[] with score/reason, "intent": Intent, "meta": RecommendationMeta }`。服务端先过滤过期活动、城市、日期、时段、人数、预算和距离，再按确定性分数排序。`reason` 只引用服务端活动事实。

`RecommendationMeta` 包含 `rankVersion`、`candidateCount`、`matchedCount` 和 `hardFilters`，用于页面解释和离线评测，不代表匹配概率或线上转化率。

## `GET /healthz`

返回 `status`、`database`、`aiConfigured` 和 `model`。不会返回 `ZHIPU_API_KEY` 或原始用户输入。
