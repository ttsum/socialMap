const test = require('node:test')
const assert = require('node:assert/strict')

let mode = 'api'
let requests = []
global.getApp = () => ({ globalData: { mode, apiBaseUrl: 'http://127.0.0.1:8000/api/v1' } })
global.wx = {
  request(options) {
    requests.push(options)
    if (options.url.includes('/activities/?category=')) {
      options.success({ statusCode: 200, data: { items: [{ id: 'a-walk' }] } })
      return
    }
    if (options.url.includes('/recommendations/')) {
      options.success({ statusCode: 200, data: { items: [{ id: 'a-walk', score: 90 }], intent: options.data, meta: { rankVersion: 'rank-v2' } } })
      return
    }
    if (options.url.includes('/parse-intent/')) {
      if (options.data && options.data.query === '成功') {
        options.success({ statusCode: 200, data: { intent: { people: 2, uncertainFields: ['day'] }, meta: { model: 'glm-5.3', promptVersion: 'intent-v2', latencyMs: 12, fallbackUsed: false } } })
        return
      }
      options.success({ statusCode: 503, data: { detail: 'AI 服务暂时不可用' } })
      return
    }
    options.fail({ errMsg: 'request:fail simulated' })
  }
}
const api = require('../services/api')

test('API adapter exposes API mode and unwraps list/recommendation responses', async () => {
  requests = []
  assert.equal(api.enabled(), true)
  assert.deepEqual(await api.listActivities('户外'), [{ id: 'a-walk' }])
  const intent = { people: 2, city: '长沙' }
  assert.deepEqual(await api.recommend(intent), { items: [{ id: 'a-walk', score: 90 }], intent, meta: { rankVersion: 'rank-v2' } })
  assert.equal(requests[0].url, 'http://127.0.0.1:8000/api/v1/activities/?category=%E6%88%B7%E5%A4%96')
  assert.equal(requests[1].method, 'POST')
})

test('API adapter surfaces HTTP and network errors for retry UI', async () => {
  await assert.rejects(api.parseIntent('周六下午两个人'), /AI 服务暂时不可用/)
  await assert.rejects(api.getActivity('missing'), /本机 API 连接失败/)
})

test('API adapter preserves intent uncertainty and model metadata', async () => {
  assert.deepEqual(await api.parseIntent('成功'), {
    intent: { people: 2, uncertainFields: ['day'] },
    meta: { model: 'glm-5.3', promptVersion: 'intent-v2', latencyMs: 12, fallbackUsed: false }
  })
})

test('API adapter can be disabled without changing its configured URL', () => {
  mode = 'local-demo'
  assert.equal(api.enabled(), false)
  mode = 'api'
})
