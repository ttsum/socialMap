from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('activities', '0003_alter_activity_options_alter_message_options'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name='PublishRequest', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('query', models.TextField(max_length=300)), ('intent', models.JSONField(default=dict)),
        ('city', models.CharField(max_length=40)), ('location_name', models.CharField(max_length=120)),
        ('address', models.CharField(max_length=240)), ('lat', models.FloatField()), ('lng', models.FloatField()),
        ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
        ('review_note', models.TextField(blank=True, default='')), ('created_at', models.DateTimeField(auto_now_add=True)),
        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publish_requests', to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['-created_at', '-id']})]
