App({
  globalData: {
    appName: '团团团',
    // Use the local Django integration by default; switch back to local-demo for offline preview.
    mode: 'api',
    apiBaseUrl: 'http://127.0.0.1:8000/api/v1'
  }
})
