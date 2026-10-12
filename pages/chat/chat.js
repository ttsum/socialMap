const store = require('../../services/store')
const api = require('../../services/api')
const { go, error } = require('../../utils/navigation')
Page({
 data: { group: null, allowed: false, messages: [], input: '', target: '' },
 onLoad(options) { this.groupId = options.groupId },
 onShow() { this.refresh() },
 refresh() {
  const group = store.getGroup(this.groupId)
  const s = store.read()
  const allowed = !!(group && (api.enabled() ? wx.getStorageSync('tuantuantuan.api.access') : (s.loggedIn && s.joined[this.groupId])))
  const messages = allowed && !api.enabled() ? store.messages(this.groupId) : []
  this.setData({ group, allowed, messages, target: messages.length ? messages[messages.length - 1].id : '' })
  if (allowed && api.enabled()) this.loadRemoteMessages()
  if(group) wx.setNavigationBarTitle({ title: group.activity.title })
 },
 input(e) { this.setData({ input: e.detail.value }) },
  send() {
   const content = this.data.input.trim(); if (!content) return
   if (api.enabled()) return api.sendMessage(this.groupId, 'wx-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8), content).then(() => { this.setData({ input: '' }); this.loadRemoteMessages() }).catch(error)
   try { store.send(this.groupId, content); this.setData({ input: '' }); this.refresh() } catch(e) { error(e) }
  },
  loadRemoteMessages() { api.messages(this.groupId).then(items => this.setData({ messages: items.map(m => Object.assign(m, { name: m.sender_name, initial: m.sender_name ? m.sender_name.slice(0,1) : '团', mine: false, time: m.created_at.slice(11,16), type: 'text' })), target: items.length ? String(items[items.length-1].id) : '' })).catch(error) },
 quick(e) { this.setData({ input: e.currentTarget.dataset.text }) },
 detail() { if (this.data.group) go('detail', { id: this.data.group.activityId }); else go('index') },
 login() { store.requireLogin(() => this.refresh()) }
})
