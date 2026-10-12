function config() {
  const app = typeof getApp === 'function' ? getApp() : null
  return app && app.globalData ? app.globalData : {}
}

function enabled() {
  return config().mode === 'api'
}

function messageFor(payload, fallback) {
  if (!payload) return fallback
  if (typeof payload === 'string') {
    if (payload.indexOf('<!DOCTYPE html>') !== -1 || payload.indexOf('<html') !== -1) return fallback
    return payload
  }
  if (payload.detail) return payload.detail
  for (const key of Object.keys(payload)) {
    const value = payload[key]
    if (Array.isArray(value) && value.length) return String(value[0])
    if (typeof value === 'string') return value
  }
  return fallback
}

function request(path, options) {
  const settings = options || {}
  const baseUrl = String(config().apiBaseUrl || '').replace(/\/$/, '')
  return new Promise((resolve, reject) => {
    if (!baseUrl || typeof wx === 'undefined' || typeof wx.request !== 'function') {
      reject(new Error('本机 API 尚未配置'))
      return
    }
    const token = typeof wx.getStorageSync === 'function' ? (wx.getStorageSync('tuantuantuan.api.access') || '') : ''
    const headers = { 'content-type': 'application/json' }
    if (token) headers.Authorization = 'Bearer ' + token
    wx.request({
      url: baseUrl + path,
      method: settings.method || 'GET',
      data: settings.data,
      timeout: settings.timeout || 15000,
      header: Object.assign(headers, settings.header || {}),
      success(response) {
        const body = response.data
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(body)
          return
        }
        const error = new Error(messageFor(body, '本机 API 请求失败'))
        error.statusCode = response.statusCode
        error.payload = body
        reject(error)
      },
      fail(error) {
        const detail = error && error.errMsg ? '：' + error.errMsg : ''
        reject(new Error('本机 API 连接失败' + detail))
      }
    })
  })
}

function login() {
  return new Promise((resolve, reject) => {
    if (!wx.login) return reject(new Error('当前环境不支持微信登录'))
    wx.login({
      success: result => {
        if (!result.code) return reject(new Error('微信登录未取得 code'))
        request('/auth/wechat/', { method: 'POST', data: { code: result.code } }).then(body => {
          wx.setStorageSync('tuantuantuan.api.access', body.access)
          wx.setStorageSync('tuantuantuan.api.refresh', body.refresh)
          wx.setStorageSync('tuantuantuan.api.user', body.user || null)
          resolve(body.user || null)
        }).catch(reject)
      },
      fail: err => reject(new Error('微信登录失败：' + (err.errMsg || '未知错误')))
    })
  })
}
function logout() {
  const refresh = wx.getStorageSync('tuantuantuan.api.refresh')
  return request('/auth/logout/', { method: 'POST', data: { refresh } }).catch(() => null).then(() => {
    wx.removeStorageSync('tuantuantuan.api.access'); wx.removeStorageSync('tuantuantuan.api.refresh'); wx.removeStorageSync('tuantuantuan.api.user')
  })
}
function join(groupId, seats) { return request('/groups/' + encodeURIComponent(groupId) + '/membership/', { method: 'PUT', data: { seats } }) }
function leave(groupId) { return request('/groups/' + encodeURIComponent(groupId) + '/membership/', { method: 'DELETE' }) }
function favorite(activityId, value) { return request('/activities/' + encodeURIComponent(activityId) + '/favorite/', { method: value ? 'PUT' : 'DELETE' }) }
function messages(groupId) { return request('/groups/' + encodeURIComponent(groupId) + '/messages/').then(body => body.items || []) }
function sendMessage(groupId, clientId, content) { return request('/groups/' + encodeURIComponent(groupId) + '/messages/', { method: 'POST', data: { client_id: clientId, content } }) }
function meGroups() { return request('/me/groups/').then(body => body.items || []) }
function meFavorites() { return request('/me/favorites/').then(body => body.items || []) }
function conversations() { return request('/conversations/').then(body => body.items || []) }
function searchLocations(keywords, city) { return request('/locations/search/?keywords=' + encodeURIComponent(keywords) + (city ? '&city=' + encodeURIComponent(city) : '')).then(body => body.items || []) }
function geocodeLocation(address, city) { return request('/locations/geocode/?address=' + encodeURIComponent(address) + (city ? '&city=' + encodeURIComponent(city) : '')).then(body => body.items || []) }
function publishRequest(query, intent, location) { return request('/publish-requests/', { method: 'POST', data: { query, intent, location }, timeout: 15000 }) }

function listActivities(category) {
  const query = category && category !== '全部' ? '?category=' + encodeURIComponent(category) : ''
  return request('/activities/' + query).then(body => body.items || [])
}

function getActivity(id) {
  return request('/activities/' + encodeURIComponent(id) + '/').then(body => body)
}

function parseIntent(query) {
  return request('/ai/parse-intent/', { method: 'POST', data: { query }, timeout: 45000 }).then(body => ({ intent: body.intent, meta: body.meta || null }))
}

function recommend(intent) {
  return request('/recommendations/', { method: 'POST', data: intent }).then(body => ({ items: body.items || [], intent: body.intent, meta: body.meta || null }))
}

module.exports = { enabled, request, listActivities, getActivity, parseIntent, recommend, login, logout, join, leave, favorite, messages, sendMessage, meGroups, meFavorites, conversations, searchLocations, geocodeLocation, publishRequest }
