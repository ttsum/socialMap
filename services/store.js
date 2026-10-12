const activities = require('../data/activities')
const groups = require('../data/groups')
const members = require('../data/members')
const initialMessages = require('../data/messages')
const { validate } = require('../data/mock-ai')
const api = require('./api')
const KEY = 'tuantuantuan.demo.v1'
const empty = () => ({ loggedIn: false, favorites: [], joined: {}, messages: {}, draft: '', intent: null, intentMeta: null })
function read() {
  const raw = wx.getStorageSync(KEY)
  if (!raw || typeof raw !== 'object' || !Array.isArray(raw.favorites) || !raw.joined || !raw.messages) return empty()
  return Object.assign(empty(), raw)
}
function save(state) { wx.setStorageSync(KEY, state); return state }
function update(fn) { const s = read(); fn(s); return save(s) }
function timeLabel(timestamp) {
  const d = new Date(timestamp)
  const pad = n => String(n).padStart(2, '0')
  return (d.getMonth() + 1) + '/' + d.getDate() + ' 周' + '日一二三四五六'[d.getDay()] + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes())
}
function list() {
  const s = read()
  return activities.map(a => {
    const g = groups.find(x => x.activityId === a.id)
    const joinedSeats = Number(s.joined[g.id]) || 0
    const joinedCount = g.memberIds.length + joinedSeats
    return Object.assign({}, a, {
      groupId: g.id, joinedCount, joinedSeats, remaining: Math.max(0, a.capacity - joinedCount),
      joined: joinedSeats > 0, favorite: s.favorites.indexOf(a.id) >= 0,
      dateLabel: timeLabel(a.startTime), priceLabel: a.pricePerPerson === 0 ? '免费' : '¥' + a.pricePerPerson + '/人'
    })
  })
}
function decorateRemoteActivity(activity) {
  if (!activity) return null
  const s = read()
  const group = groups.find(item => item.id === activity.groupId)
  const groupId = activity.groupId || (group && group.id)
  const joinedSeats = groupId ? Number(s.joined[groupId]) || 0 : 0
  const baseJoinedCount = Number(activity.joinedCount) || (group ? group.memberIds.length : 0)
  const joinedCount = baseJoinedCount + joinedSeats
  return Object.assign({}, activity, {
    groupId,
    joinedCount,
    joinedSeats,
    remaining: Math.max(0, Number(activity.capacity) - joinedCount),
    joined: joinedSeats > 0,
    favorite: s.favorites.indexOf(activity.id) >= 0,
    priceLabel: activity.priceLabel || (Number(activity.pricePerPerson) === 0 ? '免费' : '¥' + activity.pricePerPerson + '/人')
  })
}
function decorateRemoteActivities(items) { return (items || []).map(decorateRemoteActivity) }
function getActivity(id) { return list().find(a => a.id === id) }
function getGroup(id) {
  const group = groups.find(g => g.id === id)
  if (!group) return null
  return Object.assign({}, group, { members: group.memberIds.map(id => members.find(m => m.id === id)), activity: getActivity(group.activityId) })
}
function recommend(intent) {
  if (validate(intent)) return []
  return list().filter(a => {
    const day = '周' + '日一二三四五六'[new Date(a.startTime).getDay()]
    const hour = new Date(a.startTime).getHours()
    const period = hour < 12 ? '上午' : hour < 18 ? '下午' : '晚上'
    return a.city === intent.city && a.startTime > Date.now() &&
      a.remaining + a.joinedSeats >= Number(intent.people) &&
      a.pricePerPerson <= Number(intent.budgetPerPerson) && a.distanceKm <= Number(intent.maxDistanceKm) &&
      (intent.day === '不限' || day === intent.day) && (intent.period === '不限' || period === intent.period)
  }).map(a => {
    const hits = (intent.preferences || []).filter(p => a.tags.indexOf(p) >= 0)
    const score = Math.round(70 + 20 * (1 - a.distanceKm / Number(intent.maxDistanceKm)) + Math.min(10, hits.length * 5))
    const reason = '距示例位置 ' + a.distanceKm + ' 公里 · ' + a.priceLabel + ' · 可安排 ' + intent.people + ' 人' +
      (hits.length ? ' · 标签符合：' + hits.join('、') : '')
    return Object.assign({}, a, { score, reason })
  }).sort((a, b) => b.score - a.score || a.distanceKm - b.distanceKm)
}
function login() { update(s => { s.loggedIn = true }) }
function logout() { update(s => { s.loggedIn = false }) }
function requireLogin(action) {
  if (api.enabled()) {
    if (wx.getStorageSync('tuantuantuan.api.access')) { action(); return }
    wx.showModal({ title: '微信登录后继续', content: '将使用当前微信身份登录团团团。', confirmText: '微信登录', success: res => {
      if (!res.confirm) return
      api.login().then(action).catch(error => wx.showToast({ title: error.message || '登录失败', icon: 'none' }))
    } })
    return
  }
  if (read().loggedIn) { action(); return }
  wx.showModal({ title: '使用演示身份继续', content: '登录演示身份后可加入、收藏和聊天。记录仅保存在本机，不会进行微信授权或真实报名。', confirmText: '进入演示', success: res => { if (res.confirm) { login(); action() } } })
}
function toggleFavorite(id) {
  if (!getActivity(id)) throw new Error('活动不存在')
  update(s => { if (!s.loggedIn) throw new Error('请先进入演示身份'); const i = s.favorites.indexOf(id); if (i < 0) s.favorites.push(id); else s.favorites.splice(i, 1) })
}
function join(id, seats) {
  const g = getGroup(id)
  if (!read().loggedIn) throw new Error('请先进入演示身份')
  if (!g) throw new Error('拼团不存在')
  if (g.activity.joined) return
  if (g.activity.startTime <= Date.now()) throw new Error('活动已经开始，请选择其他拼团')
  if (!Number.isInteger(seats) || seats < 1 || seats > g.activity.remaining) throw new Error('剩余名额不足，请调整人数')
  update(s => {
    s.joined[id] = seats
    if (!s.messages[id]) s.messages[id] = []
    s.messages[id].push({ id: 'join-' + Date.now(), type: 'system', content: '你已加入本地演示拼团，共 ' + seats + ' 人。' })
  })
}
function leave(id) { update(s => { delete s.joined[id] }) }
function messages(id) {
  const g = getGroup(id)
  if (!g) return []
  return initialMessages(g, g.activity).concat(read().messages[id] || []).map(m => {
    const member = members.find(x => x.id === m.senderId)
    return Object.assign({}, m, { name: m.senderId === 'me' ? '我' : member ? member.name : '系统', initial: member ? member.initial : '我', mine: m.senderId === 'me' })
  })
}
function send(id, text) {
  const content = text.trim()
  if (!content || content.length > 500) throw new Error('消息请填写 1 至 500 个字')
  const s = read()
  if (!s.loggedIn || !s.joined[id] || !getGroup(id)) throw new Error('请先加入拼团')
  update(state => {
    if (!state.messages[id]) state.messages[id] = []
    state.messages[id].push({ id: 'm-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7), senderId: 'me', type: 'text', content, time: timeLabel(Date.now()) })
  })
}
function conversations() {
  const s = read()
  if (!s.loggedIn) return []
  return list().filter(a => a.joined).map(a => {
    const all = messages(a.groupId)
    return Object.assign({}, a, { preview: all[all.length - 1].content })
  })
}
module.exports = { read, update, list, decorateRemoteActivity, decorateRemoteActivities, getActivity, getGroup, recommend, login, logout, requireLogin, toggleFavorite, join, leave, messages, send, conversations, timeLabel }
