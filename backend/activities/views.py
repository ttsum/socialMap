from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.contrib.auth.models import User
from .models import Group, GroupMembership, Favorite, Message, PublishRequest
from rest_framework.exceptions import NotFound
from .models import Activity
from .serializers import ActivitySerializer, GroupDetailSerializer
from .services import recommend_with_meta, validate_intent


class ActivityListView(APIView):
    def get(self, request):
        queryset = Activity.objects.select_related('group').prefetch_related('group__members', 'group__memberships')
        category = request.query_params.get('category')
        if category and category != '全部':
            queryset = queryset.filter(category=category)
        return Response({'items': ActivitySerializer(queryset, many=True, context={'request': request}).data})


class ActivityDetailView(APIView):
    def get(self, request, activity_id):
        try:
            activity = Activity.objects.select_related('group').prefetch_related('group__members', 'group__memberships').get(pk=activity_id)
        except Activity.DoesNotExist:
            raise NotFound('活动不存在')
        return Response({'activity': ActivitySerializer(activity, context={'request': request}).data, 'group': GroupDetailSerializer(activity.group, context={'request': request}).data if hasattr(activity, 'group') else None})


class RecommendationView(APIView):
    def post(self, request):
        activities, metadata, meta = recommend_with_meta(request.data)
        payload = ActivitySerializer(activities, many=True, context={'request': request}).data
        for item in payload:
            item['score'] = metadata[item['id']]['score']
            item['reason'] = metadata[item['id']]['reason']
        return Response({'items': payload, 'intent': validate_intent(request.data), 'meta': meta})


class MembershipView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, group_id):
        seats = request.data.get('seats', 1)
        try: seats = int(seats)
        except (TypeError, ValueError): return Response({'detail': 'seats 必须是整数'}, status=400)
        with transaction.atomic():
            try: group = Group.objects.select_related('activity').get(pk=group_id)
            except Group.DoesNotExist: raise NotFound('拼团不存在')
            if group.activity.start_time <= timezone.now(): return Response({'detail': '活动已经开始'}, status=409)
            existing = GroupMembership.objects.filter(group=group, user=request.user).first()
            if existing: return Response({'detail': '已经加入，请勿重复提交'}, status=409)
            used = group.members.count() + sum(x.seats for x in group.memberships.all())
            if seats < 1 or used + seats > group.activity.capacity: return Response({'detail': '剩余名额不足'}, status=409)
            GroupMembership.objects.create(group=group, user=request.user, seats=seats)
        return Response({'group_id': group_id, 'seats': seats}, status=201)
    def delete(self, request, group_id):
        deleted, _ = GroupMembership.objects.filter(group_id=group_id, user=request.user).delete()
        if not deleted: return Response({'detail': '尚未加入该拼团'}, status=404)
        return Response(status=204)


class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, activity_id):
        try: activity = Activity.objects.get(pk=activity_id)
        except Activity.DoesNotExist: raise NotFound('活动不存在')
        Favorite.objects.get_or_create(user=request.user, activity=activity)
        return Response({'activity_id': activity_id, 'favorite': True})
    def delete(self, request, activity_id):
        Favorite.objects.filter(user=request.user, activity_id=activity_id).delete()
        return Response({'activity_id': activity_id, 'favorite': False})


class GroupMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    def _group(self, request, group_id):
        try: group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist: raise NotFound('拼团不存在')
        if not GroupMembership.objects.filter(group=group, user=request.user).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('加入拼团后才能查看群聊')
        return group
    def get(self, request, group_id):
        group = self._group(request, group_id)
        qs = group.messages.select_related('user').order_by('created_at')
        return Response({'items': [{'id': m.id, 'client_id': m.client_id, 'content': m.content, 'sender_id': m.user_id, 'sender_name': m.user.first_name or '团友', 'created_at': m.created_at.isoformat()} for m in qs]})
    def post(self, request, group_id):
        group = self._group(request, group_id)
        content = str(request.data.get('content') or '').strip()
        client_id = str(request.data.get('client_id') or '').strip()
        if not content or len(content) > 500 or not client_id or len(client_id) > 80: return Response({'detail': '消息内容和 client_id 必填，内容最多 500 字'}, status=400)
        message, _ = Message.objects.get_or_create(group=group, user=request.user, client_id=client_id, defaults={'content': content})
        return Response({'id': message.id, 'client_id': message.client_id, 'content': message.content, 'sender_id': message.user_id, 'created_at': message.created_at.isoformat()}, status=201 if message.id else 200)


class MeGroupsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        memberships = GroupMembership.objects.filter(user=request.user).select_related('group__activity')
        items = []
        for membership in memberships:
            group = membership.group
            activity = group.activity
            items.append({
                'group_id': group.id, 'activity_id': activity.id,
                'seats': membership.seats, 'title': activity.title,
                'start_time': activity.start_time.isoformat(),
            })
        return Response({'items': items})


class MeFavoritesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        activities = Activity.objects.filter(favorites__user=request.user).select_related('group').prefetch_related('group__members', 'group__memberships')
        return Response({'items': ActivitySerializer(activities, many=True, context={'request': request}).data})


class ConversationsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        groups = Group.objects.filter(memberships__user=request.user).select_related('activity').prefetch_related('messages')
        items = []
        for group in groups:
            last = group.messages.order_by('-created_at').first()
            items.append({'group_id': group.id, 'activity_id': group.activity_id,
                          'title': group.activity.title,
                          'last_message': last.content if last else '',
                          'updated_at': last.created_at.isoformat() if last else None})
        return Response({'items': items})


class PublishRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data or {}
        query = str(data.get('query') or '').strip()
        location = data.get('location') or {}
        if not query or len(query) > 300:
            return Response({'detail': '原始需求不能为空且不能超过300字'}, status=400)
        try:
            intent = validate_intent(data.get('intent') or data)
            lat, lng = float(location.get('lat')), float(location.get('lng'))
        except (TypeError, ValueError):
            return Response({'detail': '请提供有效的需求条件和地图位置'}, status=400)
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return Response({'detail': '地图坐标无效'}, status=400)
        if not location.get('name') or not location.get('address'):
            return Response({'detail': '请选择具体地点和地址'}, status=400)
        item = PublishRequest.objects.create(user=request.user, query=query, intent=intent, city=intent['city'], location_name=str(location['name'])[:120], address=str(location['address'])[:240], lat=lat, lng=lng)
        return Response({'id': item.id, 'status': item.status, 'created_at': item.created_at.isoformat()}, status=201)

    def get(self, request):
        items = PublishRequest.objects.filter(user=request.user)
        return Response({'items': [{'id': x.id, 'query': x.query, 'intent': x.intent, 'city': x.city, 'location_name': x.location_name, 'address': x.address, 'lat': x.lat, 'lng': x.lng, 'status': x.status, 'created_at': x.created_at.isoformat()} for x in items]})
