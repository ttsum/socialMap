from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('activities', '0001_initial'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Favorite', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to='activities.activity')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='GroupMembership', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('seats', models.PositiveIntegerField(default=1)),
            ('joined_at', models.DateTimeField(auto_now_add=True)),
            ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='activities.group')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='Message', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('client_id', models.CharField(max_length=80)),
            ('content', models.TextField(max_length=500)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='activities.group')),
            ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.AddConstraint(model_name='favorite', constraint=models.UniqueConstraint(fields=('user','activity'), name='unique_favorite')),
        migrations.AddConstraint(model_name='groupmembership', constraint=models.UniqueConstraint(fields=('group','user'), name='unique_group_user')),
        migrations.AddConstraint(model_name='message', constraint=models.UniqueConstraint(fields=('group','user','client_id'), name='unique_message_client_id')),
    ]
