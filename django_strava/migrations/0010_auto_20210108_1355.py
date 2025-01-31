# Generated by Django 3.1.5 on 2021-01-08 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0009_auto_20210108_0004'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='external_id',
        ),
        migrations.AddField(
            model_name='activity',
            name='average_cadence',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='average_heartrate',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='average_temp',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='average_watts',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='calories',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='description',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='device_watts',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='activity',
            name='gear_id',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='has_heartrate',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='activity',
            name='has_kudoed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='activity',
            name='kilojoules',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='location_country',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='max_heartrate',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='max_watts',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='perceived_exertion',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='pr_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='prefer_perceived_exertion',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='activity',
            name='start_latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='start_longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='utc_offset',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='visibility',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='activity',
            name='weighted_average_watts',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='achievement_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='athlete_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='comment_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='device_name',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='kudos_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='photo_count',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='timezone',
            field=models.CharField(max_length=1024, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='total_photo_count',
            field=models.IntegerField(null=True),
        ),
    ]
