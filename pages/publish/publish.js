const store = require('../../services/store')
const ai = require('../../data/mock-ai')
const api = require('../../services/api')
const { go, error } = require('../../utils/navigation')

Page({
 data: { query: '', examples: [ai.DEFAULT_QUERY, '周六上午两个人，五公里内，人均50元，想去徒步', '周日晚上两个人，人均60元，三公里内看电影'], location: null, locationQuery: '', locationResults: [], publishing: false, submitting: false, searchingLocation: false, errorMessage: '' },
 onLoad(options) { this.publishing = options && options.publish === '1' },
 onShow() { const draft = store.read(); this.setData({ query: draft.draft || '', location: draft.publishLocation || null }) },
 input(e) { this.setData({ query: e.detail.value }) },
 example(e) { this.setData({ query: this.data.examples[e.currentTarget.dataset.index] }) },
 locationInput(e) { this.setData({ locationQuery: e.detail.value }) },
 searchLocation() {
  const q = this.data.locationQuery.trim(); if (!q || this.data.searchingLocation) return
  if (!api.enabled()) { const location = { name: q, address: q, city: '长沙', lat: 28.2282, lng: 112.9388 }; this.setData({ location, locationResults: [] }); return }
  this.setData({ searchingLocation: true, errorMessage: '' })
  api.searchLocations(q, '长沙').then(items => this.setData({ locationResults: items, searchingLocation: false })).catch(err => this.setData({ searchingLocation: false, errorMessage: err.message || '地点搜索失败' }))
 },
 selectLocation(e) { const location = this.data.locationResults[Number(e.currentTarget.dataset.index)]; if (!location) return; this.setData({ location, locationResults: [] }); store.update(s => { s.publishLocation = location }) },
 onHide() { store.update(s => { s.draft = this.data.query; s.publishLocation = this.data.location }) },
 submit() {
  const query = this.data.query.trim(); if (!query) return error(new Error('先写下你想参加的活动'))
  if (api.enabled() && !this.data.location) { this.setData({ errorMessage: '请先搜索并选择具体地点' }); return }
  if (api.enabled()) { if (this.data.submitting) return; store.update(s => { s.draft = query }); this.setData({ submitting: true, errorMessage: '' }); const action = this.publishing ? api.publishRequest(query, store.read().intent || {}, this.data.location) : api.parseIntent(query); action.then(result => { if (this.publishing) { wx.showToast({ title: '需求已提交审核', icon: 'success' }); this.setData({ submitting: false }); return } const parsed = result && result.intent ? result : { intent: result, meta: null }; store.update(s => { s.intent = parsed.intent; s.intentMeta = parsed.meta; s.publishLocation = this.data.location }); go('confirm') }).catch(err => this.setData({ submitting: false, errorMessage: err.message || '请求失败，请重试' })); return }
  store.update(s => { s.draft = query; s.intent = ai.parse(query); s.intentMeta = { model: 'local-rule-v1', promptVersion: 'local-demo', latencyMs: 0, fallbackUsed: false } }); go('confirm')
 },
 retry() { this.submit() }
})
