from django.contrib import admin
from .models import Activity, Group, PublishRequest

admin.site.register(Activity)
admin.site.register(Group)
@admin.register(PublishRequest)
class PublishRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'city', 'location_name', 'status', 'created_at')
    list_filter = ('status', 'city')
