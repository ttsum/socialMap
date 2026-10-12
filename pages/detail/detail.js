const store = require('../../services/store')
const api = require('../../services/api')
const { go, error } = require('../../utils/navigation')
Page({
 data: { activity: null, group: null, seats: 1, availableSeats: [], seatIndex: 0, reason: '', loading: false, errorMessage: '' },
 onLoad(options) { this.id = options.id; this.source = options.source; this.requestedSeats = Number(options.people) || 1 },
 onShow() { this.refresh() },
 refresh() {
  if (api.enabled()) return this.load()
  this.applyActivity(store.getActivity(this.id), store.getGroup((store.getActivity(this.id) || {}).groupId))
 },
 applyActivity(a, remoteGroup) {
  if (!a) { this.setData({ activity: null, group: null, loading: false, errorMessage: '' }); return }
  const seats = a.joinedSeats || this.requestedSeats
  const availableSeats = Array.from({ length: Math.max(1, a.remaining) }, (_, i) => i + 1)
  const result = this.source === 'matches' && store.read().intent ? store.recommend(store.read().intent).find(x => x.id === a.id) : null
  const group = remoteGroup || store.getGroup(a.groupId)
  if (group) group.activity = a
  this.setData({ activity: a, group, seats, availableSeats, seatIndex: Math.max(0, availableSeats.indexOf(seats)), reason: a.reason || (result ? result.reason : ''), loading: false, errorMessage: '' })
 },
 load() {
  const token = (this.loadToken || 0) + 1
  this.loadToken = token
  this.setData({ loading: true, errorMessage: '' })
  api.getActivity(this.id).then(result => {
   if (token !== this.loadToken) return
   const activity = store.decorateRemoteActivity(result.activity)
   const group = result.group || null
   this.applyActivity(activity, group)
  }).catch(err => {
   if (token !== this.loadToken) return
   this.setData({ activity: null, group: null, loading: false, errorMessage: err.message || '活动详情加载失败' })
  })
 },
 retry() { this.refresh() },
 count(e) { const i = Number(e.detail.value); this.requestedSeats = this.data.availableSeats[i]; this.setData({ seats: this.requestedSeats, seatIndex: i }) },
  favorite() { store.requireLogin(() => {
    if (api.enabled()) return api.favorite(this.id, !this.data.activity.favorite).then(() => this.refresh()).catch(error)
    try { store.toggleFavorite(this.id); this.refresh() } catch(e) { error(e) }
  }) },
 join() {
  store.requireLogin(() => {
    const a = api.enabled() ? this.data.activity : store.getActivity(this.id)
    if (!a) return error(new Error('活动不存在'))
    if (a.joined) return go('chat', { groupId: a.groupId })
    wx.showModal({ title: '确认加入演示拼团', content: '为你和同行伙伴占用 ' + this.data.seats + ' 个演示名额。此操作仅保存在本机，不产生订单或真实报名。', confirmText: '确认加入', success: res => {
      if (!res.confirm) return
      if (api.enabled()) {
       api.join(a.groupId, this.data.seats).then(() => { this.refresh(); go('chat', { groupId: a.groupId }) }).catch(error)
       return
      }
      try { store.join(a.groupId, this.data.seats); this.refresh(); go('chat', { groupId: a.groupId }) } catch (e) { error(e) }
    } })
  })
 },
  leave() { wx.showModal({ title: '退出这个拼团？', content: '将释放你和同行伙伴的名额。', confirmText: '退出拼团', success: res => { if(!res.confirm) return; if (api.enabled()) { api.leave(this.data.activity.groupId).then(() => { this.requestedSeats = 1; this.refresh() }).catch(error); return } try { store.leave(this.data.activity.groupId); this.requestedSeats = 1; this.refresh() } catch (e) { error(e) } } }) },
 home() { go('index') },
 onShareAppMessage() { const a = this.data.activity; return { title: a ? a.title + ' · 团团团演示' : '团团团', path: a ? '/pages/detail/detail?id=' + a.id : '/pages/index/index' } }
})
