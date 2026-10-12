import json
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from .provider import GLMProvider, ProviderError
from .service import parse_query, parse_query_with_meta


def response(content):
    return {'choices': [{'message': {'content': json.dumps(content, ensure_ascii=False)}}]}


class ProviderTests(SimpleTestCase):
    def test_json_success(self):
        calls = []
        provider = GLMProvider(api_key='test', transport=lambda model, payload: (200, response({'people': 2})))
        data, model = provider.complete_json([])
        self.assertEqual(data['people'], 2)
        self.assertEqual(model, 'glm-5.3')

    def test_model_unavailable_falls_back_once(self):
        calls = []
        def transport(model, payload):
            calls.append(model)
            if model == 'glm-5.3':
                raise ProviderError('model not found', status=404, model=model)
            return 200, response({'people': 2})
        data, model = GLMProvider(api_key='test', transport=transport).complete_json([])
        self.assertEqual(calls, ['glm-5.3', 'glm-5.2'])
        self.assertEqual(model, 'glm-5.2')

    def test_non_model_error_does_not_fallback(self):
        calls = []
        def transport(model, payload):
            calls.append(model)
            raise ProviderError('rate limited', status=429, model=model)
        with self.assertRaises(ProviderError):
            GLMProvider(api_key='test', transport=transport).complete_json([])
        self.assertEqual(calls, ['glm-5.3'])

    def test_invalid_json_is_rejected(self):
        provider = GLMProvider(api_key='test', transport=lambda model, payload: (200, {'choices': [{'message': {'content': '{bad'}}]}))
        with self.assertRaises(ProviderError):
            provider.complete_json([])

    def test_missing_response_shape_is_rejected(self):
        provider = GLMProvider(api_key='test', transport=lambda model, payload: (200, response({'people': 2})))
        with self.assertRaises(ValidationError):
            parse_query('周六下午两个人', provider=provider)

    def test_parse_query_validates_and_keeps_model(self):
        content = {
            'query': '周六下午两个人', 'people': 2, 'day': '周六', 'period': '下午',
            'maxDistanceKm': 5, 'budgetPerPerson': 100, 'preferences': ['安静'],
            'city': '长沙', 'notes': [], 'uncertainFields': [],
        }
        provider = GLMProvider(api_key='test', transport=lambda model, payload: (200, response(content)))
        intent, meta = parse_query_with_meta('周六下午两个人', provider=provider)
        self.assertEqual(intent['people'], 2)
        self.assertEqual(intent['uncertainFields'], [])
        self.assertEqual(intent['query'], '周六下午两个人')
        self.assertEqual(meta['model'], 'glm-5.3')
        self.assertEqual(meta['promptVersion'], 'intent-v2')

    def test_parse_query_keeps_uncertainty_fields(self):
        content = {
            'query': '明天找活动', 'people': 1, 'day': '不限', 'period': '不限',
            'maxDistanceKm': 5, 'budgetPerPerson': 100, 'preferences': [],
            'city': '长沙', 'notes': ['日期不确定'], 'uncertainFields': ['day', 'period'],
        }
        provider = GLMProvider(api_key='test', transport=lambda model, payload: (200, response(content)))
        intent = parse_query('明天找活动', provider=provider)
        self.assertEqual(intent['uncertainFields'], ['day', 'period'])
