import json
import urllib.parse
import urllib.request
from django.conf import settings

class WeChatLoginError(Exception):
    pass

def code2session(code):
    if not settings.WECHAT_APPSECRET:
        raise WeChatLoginError('未配置 WECHAT_APPSECRET')
    query = urllib.parse.urlencode({'appid': settings.WECHAT_APPID, 'secret': settings.WECHAT_APPSECRET, 'js_code': code, 'grant_type': 'authorization_code'})
    try:
        with urllib.request.urlopen(settings.WECHAT_CODE2SESSION_URL + '?' + query, timeout=8) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        raise WeChatLoginError('微信登录服务连接失败') from exc
    if payload.get('errcode'):
        raise WeChatLoginError('微信登录失败：' + str(payload.get('errmsg', payload['errcode'])))
    if not payload.get('openid') or not payload.get('session_key'):
        raise WeChatLoginError('微信登录响应缺少身份字段')
    return payload
