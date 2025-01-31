# Generated by Django 3.1.5 on 2021-01-08 04:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0006_auto_20210107_1554'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('external_id', models.CharField(max_length=1024, null=True)),
                ('upload_id', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=1024, null=True)),
                ('type', models.CharField(max_length=200, null=True)),
                ('start_date', models.DateTimeField(null=True)),
                ('start_date_local', models.DateTimeField(null=True)),
                ('distance', models.FloatField(null=True)),
                ('moving_time', models.IntegerField(null=True)),
                ('elapsed_time', models.IntegerField(null=True)),
                ('total_elevation_gain', models.FloatField(null=True)),
                ('athlete', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='strava.stravaathlete')),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='ActivityDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_name', models.CharField(max_length=300, null=True)),
                ('activity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='strava.activity')),
            ],
        ),
        migrations.CreateModel(
            name='ActivityStream',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.JSONField()),
                ('distance', models.JSONField()),
                ('latlng', models.JSONField(blank=True)),
                ('altitude', models.JSONField(blank=True)),
                ('heartrate', models.JSONField(blank=True)),
                ('cadence', models.JSONField(blank=True)),
                ('watts', models.JSONField(blank=True)),
                ('temp', models.JSONField(blank=True)),
                ('activity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='strava.activity')),
            ],
        ),
        migrations.CreateModel(
            name='ActivitySummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('elev_high', models.FloatField(null=True)),
                ('elev_low', models.FloatField(null=True)),
                ('timezone', models.CharField(max_length=1014, null=True)),
                ('achievement_count', models.IntegerField(default=0)),
                ('kudos_count', models.IntegerField(default=0)),
                ('comment_count', models.IntegerField(default=0)),
                ('athlete_count', models.IntegerField(default=0)),
                ('photo_count', models.IntegerField(default=0)),
                ('total_photo_count', models.IntegerField(default=0)),
                ('trainer', models.BooleanField(default=False)),
                ('commute', models.BooleanField(default=False)),
                ('manual', models.BooleanField(default=False)),
                ('private', models.BooleanField(default=False)),
                ('flagged', models.BooleanField(default=False)),
                ('workout_type', models.IntegerField(null=True)),
                ('average_speed', models.FloatField(null=True)),
                ('max_speed', models.FloatField(null=True)),
                ('activity', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='strava.activity')),
            ],
        ),
        migrations.DeleteModel(
            name='StravaActivity',
        ),
    ]
