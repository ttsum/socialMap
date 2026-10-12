from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken

from .models import Activity


class ActivityApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = APIClient()

    def auth(self):
        user = User.objects.create_user(username='api-user')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(AccessToken.for_user(user)))
        return user

    def test_activity_list_and_category_filter(self):
        response = self.client.get('/api/v1/activities/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['items']), 6)
        self.assertIn('groupId', response.data['items'][0])
        self.assertIn('priceLabel', response.data['items'][0])

        response = self.client.get('/api/v1/activities/?category=户外')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item['category'] for item in response.data['items']}, {'户外'})
        self.assertEqual(len(response.data['items']), 2)

    def test_activity_detail_includes_group_members_and_rules(self):
        response = self.client.get('/api/v1/activities/a-walk/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['activity']['id'], 'a-walk')
        self.assertEqual(response.data['group']['id'], 'g-walk')
        self.assertEqual(len(response.data['group']['members']), 3)
        self.assertTrue(response.data['group']['rules'])

    def test_missing_activity_returns_not_found(self):
        response = self.client.get('/api/v1/activities/missing/')
        self.assertEqual(response.status_code, 404)

    def test_recommendation_applies_hard_filters_and_returns_reason(self):
        intent = {
            'people': 4,
            'day': '周六',
            'period': '下午',
            'maxDistanceKm': 5,
            'budgetPerPerson': 100,
            'preferences': ['安静'],
            'city': '长沙',
        }
        response = self.client.post('/api/v1/recommendations/', intent, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['items'])
        self.assertEqual(response.data['meta']['rankVersion'], 'rank-v2')
        self.assertEqual(response.data['meta']['hardFilters'], ['city', 'time', 'capacity', 'budget', 'distance'])
        for item in response.data['items']:
            self.assertLessEqual(item['distanceKm'], 5)
            self.assertLessEqual(item['pricePerPerson'], 100)
            self.assertGreaterEqual(item['remaining'], 4)
            self.assertIsInstance(item['score'], int)
            self.assertIn('距示例位置', item['reason'])

        empty = dict(intent, city='上海')
        response = self.client.post('/api/v1/recommendations/', empty, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['items'], [])
        self.assertEqual(response.data['meta']['matchedCount'], 0)

    def test_started_activity_is_not_recommended(self):
        activity = Activity.objects.get(pk='a-walk')
        activity.start_time = timezone.now() - timedelta(minutes=1)
        activity.save(update_fields=['start_time'])
        response = self.client.post('/api/v1/recommendations/', {
            'people': 1,
            'day': '不限',
            'period': '不限',
            'maxDistanceKm': 100,
            'budgetPerPerson': 100,
            'preferences': [],
            'city': '长沙',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('a-walk', [item['id'] for item in response.data['items']])

    def test_invalid_recommendation_parameters_return_bad_request(self):
        response = self.client.post('/api/v1/recommendations/', {
            'people': 0,
            'day': '周六',
            'period': '下午',
            'maxDistanceKm': 5,
            'budgetPerPerson': 100,
            'preferences': [],
            'city': '长沙',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_health_check_does_not_expose_secret(self):
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['database'], 'ok')
        self.assertNotIn('apiKey', payload)
        self.assertNotIn('input', payload)

    def test_membership_favorite_and_message_are_authenticated_and_idempotent(self):
        self.auth()
        response = self.client.put('/api/v1/groups/g-walk/membership/', {'seats': 2}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.put('/api/v1/groups/g-walk/membership/', {'seats': 2}, format='json').status_code, 409)
        self.assertEqual(self.client.put('/api/v1/activities/a-walk/favorite/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/activities/a-walk/').data['activity']['favorite'], True)
        message = self.client.post('/api/v1/groups/g-walk/messages/', {'client_id': 'm-1', 'content': '周末见'}, format='json')
        self.assertEqual(message.status_code, 201)
        duplicate = self.client.post('/api/v1/groups/g-walk/messages/', {'client_id': 'm-1', 'content': '重复'}, format='json')
        self.assertEqual(duplicate.status_code, 201)
        self.assertEqual(self.client.get('/api/v1/groups/g-walk/messages/').data['items'][0]['content'], '周末见')
        self.assertEqual(self.client.delete('/api/v1/groups/g-walk/membership/').status_code, 204)

    def test_non_member_cannot_read_or_send_group_messages(self):
        self.auth()
        self.assertEqual(self.client.get('/api/v1/groups/g-walk/messages/').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/groups/g-walk/messages/', {'client_id': 'm-2', 'content': 'hi'}, format='json').status_code, 403)
