from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('activities', '0002_membership_favorite_message')]
    operations = [
        migrations.AlterModelOptions(name='activity', options={'ordering': ['start_time', 'id']}),
        migrations.AlterModelOptions(name='message', options={'ordering': ['created_at', 'id']}),
    ]
