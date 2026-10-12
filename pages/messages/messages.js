const store = require('../../services/store')
const api = require('../../services/api')
const { go } = require('../../utils/navigation')
Page({
 data: { loggedIn: false, conversations: [] },
 onShow() { this.refresh() },
 refresh() {
  if (api.enabled() && wx.getStorageSync('tuantuantuan.api.access')) {
   api.conversations().then(items => this.setData({ loggedIn: true, conversations: items })).catch(() => this.setData({ loggedIn: true, conversations: [] }))
   return
  }
  this.setData({ loggedIn: store.read().loggedIn, conversations: store.conversations() })
 },
 login() { store.requireLogin(() => this.refresh()) },
 open(e) { go('chat', { groupId: e.currentTarget.dataset.id }) },
 home() { go('index') }
})
