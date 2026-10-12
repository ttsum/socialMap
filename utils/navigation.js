const tabs = ['index', 'map', 'publish', 'messages', 'profile']
function go(page, params) {
  const query = Object.keys(params || {}).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(params[k])).join('&')
  const url = '/pages/' + page + '/' + page + (query ? '?' + query : '')
  const fail = () => wx.showToast({ title: '页面打开失败，请重试', icon: 'none' })
  if (tabs.indexOf(page) >= 0) wx.switchTab({ url, fail })
  else wx.navigateTo({ url, fail })
}
function error(e) { wx.showToast({ title: e.message || '操作失败，请重试', icon: 'none' }) }
module.exports = { go, error }
