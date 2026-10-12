import json
import os
import socket
import time
from urllib import request
from urllib.error import HTTPError, URLError


class ProviderError(Exception):
    def __init__(self, message, status=None, model=None):
        super().__init__(message)
        self.status = status
        self.model = model


class GLMProvider:
    def __init__(self, api_key=None, base_url=None, model=None, fallback_model=None, timeout=None, transport=None):
        self.api_key = api_key if api_key is not None else os.getenv('ZHIPU_API_KEY', '')
        self.base_url = (base_url or os.getenv('ZHIPU_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4')).rstrip('/')
        self.model = model or os.getenv('LLM_MODEL', 'glm-5.3')
        self.fallback_model = fallback_model or os.getenv('LLM_FALLBACK_MODEL', 'glm-5.2')
        self.timeout = timeout or int(os.getenv('LLM_TIMEOUT_SECONDS', '40'))
        self.transport = transport or self._transport
        self.last_meta = {
            'model': self.model,
            'promptVersion': 'intent-v2',
            'latencyMs': 0,
            'fallbackUsed': False,
        }

    def _transport(self, model, payload):
        if not self.api_key:
            raise ProviderError('未配置 ZHIPU_API_KEY', status=500, model=model)
        body = json.dumps(dict(payload, model=model)).encode('utf-8')
        req = request.Request(self.base_url + '/chat/completions', data=body, headers={'Authorization': 'Bearer ' + self.api_key, 'Content-Type': 'application/json'}, method='POST')
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return response.status, json.loads(response.read().decode('utf-8'))
        except HTTPError as error:
            try:
                detail = json.loads(error.read().decode('utf-8'))
            except Exception:
                detail = {'error': error.reason}
            raise ProviderError(str(detail), status=error.code, model=model)
        except (URLError, TimeoutError, socket.timeout) as error:
            raise ProviderError('智谱服务连接失败：' + str(error), status=503, model=model)

    def complete_json(self, messages):
        started = time.perf_counter()
        payload = {'messages': messages, 'temperature': 0.1, 'response_format': {'type': 'json_object'}}
        fallback_used = False
        try:
            status, data = self.transport(self.model, payload)
        except ProviderError as error:
            if self._is_model_unavailable(error) and self.fallback_model and self.fallback_model != self.model:
                status, data = self.transport(self.fallback_model, payload)
                used_model = self.fallback_model
                fallback_used = True
            else:
                raise
        else:
            used_model = self.model
        try:
            content = data['choices'][0]['message']['content']
            parsed = json.loads(content)
            self.last_meta = {
                'model': used_model,
                'promptVersion': 'intent-v2',
                'latencyMs': round((time.perf_counter() - started) * 1000),
                'fallbackUsed': fallback_used,
            }
            return parsed, used_model
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
            raise ProviderError('智谱返回的 JSON 无法解析：' + str(error), status=status, model=used_model)

    @staticmethod
    def _is_model_unavailable(error):
        if error.status not in (400, 404):
            return False
        text = str(error).lower()
        return any(token in text for token in ('model', 'not found', 'does not exist', '不存在'))
