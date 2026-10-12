from rest_framework import serializers
from django.utils import timezone
from .models import Activity, Group, Member


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'name', 'initial', 'color']


class ActivitySerializer(serializers.ModelSerializer):
    groupId = serializers.SerializerMethodField()
    joinedCount = serializers.SerializerMethodField()
    joinedSeats = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    dateLabel = serializers.SerializerMethodField()
    priceLabel = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()
    locationName = serializers.CharField(source='location_name')
    distanceKm = serializers.FloatField(source='distance_km')
    pricePerPerson = serializers.FloatField(source='price_per_person')
    startTime = serializers.DateTimeField(source='start_time')
    durationHours = serializers.IntegerField(source='duration_hours')
    meetingPoint = serializers.CharField(source='meeting_point')

    class Meta:
        model = Activity
        fields = ['id', 'title', 'category', 'locationName', 'address', 'city', 'lat', 'lng', 'distanceKm', 'pricePerPerson', 'capacity', 'startTime', 'durationHours', 'tags', 'theme', 'symbol', 'description', 'meetingPoint', 'groupId', 'joinedCount', 'joinedSeats', 'remaining', 'dateLabel', 'priceLabel', 'favorite']

    def _group(self, obj):
        return getattr(obj, 'group', None)

    def get_groupId(self, obj):
        group = self._group(obj)
        return group.id if group else None

    def get_joinedCount(self, obj):
        group = self._group(obj)
        return group.members.count() + sum(x.seats for x in group.memberships.all()) if group else 0

    def get_joinedSeats(self, obj):
        return 0

    def get_remaining(self, obj):
        return max(0, obj.capacity - self.get_joinedCount(obj))

    def get_dateLabel(self, obj):
        value = timezone.localtime(obj.start_time)
        return value.strftime('%m/%d 周') + '一二三四五六日'[value.weekday()] + value.strftime(' %H:%M')

    def get_priceLabel(self, obj):
        return '免费' if obj.price_per_person == 0 else '¥%s/人' % obj.price_per_person.normalize()

    def get_favorite(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.favorites.filter(user=request.user).exists())


class GroupDetailSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    hostUserId = serializers.CharField(source='host_user_id')
    joinedCount = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'activity', 'hostUserId', 'status', 'rules', 'members', 'joinedCount']

    def get_joinedCount(self, obj):
        return obj.members.count() + sum(x.seats for x in obj.memberships.all())
