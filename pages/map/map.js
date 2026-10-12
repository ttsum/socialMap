const store = require('../../services/store')
const api = require('../../services/api')
const { go } = require('../../utils/navigation')

Page({
 data: { category: '全部', categories: ['全部', '户外', '桌游', '咖啡', '观影', '阅读'], activities: [], pins: [], markers: [], selected: null, centerLat: 28.2282, centerLng: 112.9388, scale: 12, showLocation: false, loading: false, errorMessage: '' },
 onShow() { this.refresh() },
 refresh() { if (api.enabled()) return this.load(); this.applyActivities(store.list()) },
 markerData(activities) { return activities.map((a, index) => ({ id: index + 1, latitude: Number(a.lat), longitude: Number(a.lng), title: a.title, callout: { content: a.locationName || a.title, display: 'ALWAYS', padding: 8, borderRadius: 4 }, iconPath: '/assets/icons/map-active.png', width: 34, height: 34 })) },
 applyActivities(activities) {
  const filtered = (activities || []).filter(a => this.data.category === '全部' || a.category === this.data.category)
  const markers = this.markerData(filtered); const first = filtered[0]
  this.setData({ activities: filtered, pins: filtered, markers, selected: filtered[0] || null, centerLat: first ? Number(first.lat) : this.data.centerLat, centerLng: first ? Number(first.lng) : this.data.centerLng, loading: false, errorMessage: '' })
 },
 load() { const token = (this.loadToken || 0) + 1; this.loadToken = token; this.setData({ loading: true, errorMessage: '' }); api.listActivities(this.data.category).then(items => { if (token === this.loadToken) this.applyActivities(store.decorateRemoteActivities(items)) }).catch(err => { if (token === this.loadToken) this.setData({ loading: false, errorMessage: err.message || '活动加载失败' }) }) },
 retry() { this.refresh() },
 selectCategory(e) { this.setData({ category: e.currentTarget.dataset.value }); this.refresh() },
 selectMarker(e) { const index = Number(e.detail.markerId) - 1; this.setData({ selected: this.data.activities[index] || null }) },
 selectPin(e) { this.setData({ selected: this.data.activities.find(a => a.id === e.currentTarget.dataset.id) || null }) },
 regionChange() {},
 open(e) { go('detail', { id: e.detail.id }) },
 publish() { go('publish') }
})
