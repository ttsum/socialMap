const store = require('../../services/store')
const api = require('../../services/api')
const { go } = require('../../utils/navigation')
Page({
  data: { activities: [], category: '全部', categories: ['全部', '户外', '桌游', '咖啡', '观影', '阅读'], joinedCount: 0, loading: false, errorMessage: '' },
  onShow() { this.refresh() },
  refresh() {
    if (api.enabled()) return this.load()
    const all = store.list()
    this.setData({ activities: all.filter(a => this.data.category === '全部' || a.category === this.data.category), joinedCount: store.read().loggedIn ? all.filter(a => a.joined).length : 0, loading: false, errorMessage: '' })
  },
  load() {
    const token = (this.loadToken || 0) + 1
    this.loadToken = token
    this.setData({ loading: true, errorMessage: '' })
    api.listActivities(this.data.category).then(items => {
      if (token !== this.loadToken) return
      const all = store.decorateRemoteActivities(items)
      this.setData({ activities: all, joinedCount: store.read().loggedIn ? all.filter(a => a.joined).length : 0, loading: false, errorMessage: '' })
    }).catch(error => {
      if (token !== this.loadToken) return
      this.setData({ loading: false, errorMessage: error.message || '活动加载失败' })
    })
  },
  retry() { this.refresh() },
  selectCategory(e) { this.setData({ category: e.currentTarget.dataset.value }); this.refresh() },
  publish() { go('publish') },
  map() { go('map') },
  messages() { go('messages') },
  open(e) { go('detail', { id: e.detail.id }) },
  onShareAppMessage() { return { title: '团团团 · 让周末有个好去处', path: '/pages/index/index' } }
})
