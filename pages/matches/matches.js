const store = require('../../services/store')
const api = require('../../services/api')
const { go } = require('../../utils/navigation')
Page({
 data: { activities: [], intent: null, recommendMeta: null, loading: false, errorMessage: '' },
 onShow() {
  const intent = store.read().intent
  this.setData({ intent })
  if (!intent) { this.setData({ activities: [], recommendMeta: null, loading: false, errorMessage: '' }); return }
  if (api.enabled()) return this.load(intent)
  const activities = store.recommend(intent)
  this.setData({ activities, recommendMeta: { rankVersion: 'local-rule-v1', candidateCount: activities.length, matchedCount: activities.length, hardFilters: ['city', 'time', 'capacity', 'budget', 'distance'] }, loading: false, errorMessage: '' })
 },
 load(intent) {
  const token = (this.loadToken || 0) + 1
  this.loadToken = token
  this.setData({ loading: true, errorMessage: '' })
  api.recommend(intent).then(result => {
   if (token !== this.loadToken) return
   this.setData({ activities: store.decorateRemoteActivities(result.items), recommendMeta: result.meta || null, loading: false, errorMessage: '' })
  }).catch(error => {
   if (token !== this.loadToken) return
   this.setData({ activities: [], loading: false, errorMessage: error.message || '推荐加载失败' })
  })
 },
 retry() { if (this.data.intent) this.load(this.data.intent) },
 open(e) { go('detail', { id: e.detail.id, people: this.data.intent.people, source: 'matches' }) },
 edit() { wx.redirectTo({ url: '/pages/confirm/confirm' }) },
 publish() { go('publish', { publish: '1' }) },
 map() { go('map') }
})
