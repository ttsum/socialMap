const store = require('../../services/store')
const api = require('../../services/api')
const { go } = require('../../utils/navigation')
Page({
 data: { loggedIn: false, joined: [], favorites: [], selected: 'joined' },
 onShow() { this.refresh() },
 refresh() {
  if (api.enabled() && wx.getStorageSync('tuantuantuan.api.access')) {
   Promise.all([api.meGroups(), api.meFavorites()]).then(([joined, favorites]) => this.setData({ loggedIn: true, joined, favorites })).catch(() => this.setData({ loggedIn: true, joined: [], favorites: [] }))
   return
  }
  const s = store.read(); const all = store.list(); this.setData({ loggedIn: s.loggedIn, joined: s.loggedIn ? all.filter(a => a.joined) : [], favorites: s.loggedIn ? all.filter(a => a.favorite) : [] })
 },
 login() { store.requireLogin(() => this.refresh()) },
 select(e) { this.setData({ selected: e.currentTarget.dataset.value }) },
 open(e) { go('detail', { id: e.detail.id }) },
 home() { go('index') },
 messages() { go('messages') },
 logout() { wx.showModal({ title: '退出演示身份？', content: '本机的收藏、拼团和消息将保留，下次进入演示身份可以继续。', success: r => { if(r.confirm) { store.logout(); this.refresh() } } }) },
 about() { wx.showModal({ title: '关于团团团', content: 'AI-LBS 线下社交拼团演示。活动、距离、解析与群聊均为本地示例，不使用真实微信登录，不提供真实报名或支付。', showCancel: false }) }
})
