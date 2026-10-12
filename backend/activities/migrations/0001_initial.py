from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name='Activity', fields=[('id', models.CharField(max_length=64, primary_key=True, serialize=False)), ('title', models.CharField(max_length=120)), ('category', models.CharField(max_length=40)), ('location_name', models.CharField(max_length=80)), ('address', models.CharField(max_length=200)), ('city', models.CharField(default='长沙', max_length=40)), ('lat', models.FloatField()), ('lng', models.FloatField()), ('distance_km', models.FloatField()), ('price_per_person', models.DecimalField(decimal_places=2, max_digits=8)), ('capacity', models.PositiveIntegerField()), ('start_time', models.DateTimeField()), ('duration_hours', models.PositiveIntegerField()), ('tags', models.JSONField(default=list)), ('theme', models.CharField(default='mint', max_length=30)), ('symbol', models.CharField(max_length=8)), ('description', models.TextField()), ('meeting_point', models.CharField(max_length=160))]),
        migrations.CreateModel(name='Member', fields=[('id', models.CharField(max_length=64, primary_key=True, serialize=False)), ('name', models.CharField(max_length=40)), ('initial', models.CharField(max_length=4)), ('color', models.CharField(max_length=16))]),
        migrations.CreateModel(name='Group', fields=[('id', models.CharField(max_length=64, primary_key=True, serialize=False)), ('host_user_id', models.CharField(max_length=64)), ('status', models.CharField(default='open', max_length=20)), ('rules', models.JSONField(default=list)), ('activity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='group', to='activities.activity')), ('members', models.ManyToManyField(related_name='groups', to='activities.member'))]),
    ]
