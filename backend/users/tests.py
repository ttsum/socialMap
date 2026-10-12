from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from .wechat import WeChatLoginError


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('users.views.code2session')
    def test_wechat_login_issues_tokens_without_accepting_openid(self, mocked):
        mocked.return_value = {'openid': 'openid-a', 'session_key': 'private'}
        response = self.client.post('/api/v1/auth/wechat/', {'code': 'one'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.data['user']['nickname'], '团友')
        response = self.client.get('/api/v1/me/', HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['nickname'], '团友')

    @patch('users.views.code2session', side_effect=WeChatLoginError('微信登录失败'))
    def test_wechat_failure_and_missing_code(self, mocked):
        self.assertEqual(self.client.post('/api/v1/auth/wechat/', {}, format='json').status_code, 400)
        self.assertEqual(self.client.post('/api/v1/auth/wechat/', {'code': 'bad'}, format='json').status_code, 502)

    def test_me_requires_bearer_token(self):
        self.assertEqual(self.client.get('/api/v1/me/').status_code, 401)
