from django.db import models
from django.contrib.auth.models import User


class Activity(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=40)
    location_name = models.CharField(max_length=80)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=40, default='长沙')
    lat = models.FloatField()
    lng = models.FloatField()
    distance_km = models.FloatField()
    price_per_person = models.DecimalField(max_digits=8, decimal_places=2)
    capacity = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    duration_hours = models.PositiveIntegerField()
    tags = models.JSONField(default=list)
    theme = models.CharField(max_length=30, default='mint')
    symbol = models.CharField(max_length=8)
    description = models.TextField()
    meeting_point = models.CharField(max_length=160)

    class Meta:
        ordering = ['start_time', 'id']


class Member(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=40)
    initial = models.CharField(max_length=4)
    color = models.CharField(max_length=16)


class Group(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    activity = models.OneToOneField(Activity, related_name='group', on_delete=models.CASCADE)
    host_user_id = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default='open')
    rules = models.JSONField(default=list)
    members = models.ManyToManyField(Member, related_name='groups')


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, related_name='memberships', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='group_memberships', on_delete=models.CASCADE)
    seats = models.PositiveIntegerField(default=1)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'user'], name='unique_group_user')]


class Favorite(models.Model):
    user = models.ForeignKey(User, related_name='favorites', on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, related_name='favorites', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'activity'], name='unique_favorite')]


class Message(models.Model):
    group = models.ForeignKey(Group, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    client_id = models.CharField(max_length=80)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['group', 'user', 'client_id'], name='unique_message_client_id')]


class PublishRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]
    user = models.ForeignKey(User, related_name='publish_requests', on_delete=models.CASCADE)
    query = models.TextField(max_length=300)
    intent = models.JSONField(default=dict)
    city = models.CharField(max_length=40)
    location_name = models.CharField(max_length=120)
    address = models.CharField(max_length=240)
    lat = models.FloatField()
    lng = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
