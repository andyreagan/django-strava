# Generated by Django 3.1.5 on 2021-01-07 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0003_auto_20210106_2257'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEvents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_type', models.IntegerField(choices=[(1, 'Activity'), (2, 'Athlete')], help_text='Always either "activity" or "athlete."')),
                ('aspect_type', models.IntegerField(choices=[(1, 'Create'), (2, 'Update'), (3, 'Delete')], help_text='Always "create," "update," or "delete."')),
                ('object_id', models.BigIntegerField(help_text="For activity events, the activity's ID. For athlete events, the athlete's ID.")),
                ('updates', models.JSONField()),
                ('owner_id', models.BigIntegerField(help_text="The athlete's ID.")),
                ('subscription_id', models.IntegerField(help_text='The push subscription ID that is receiving this event.')),
                ('event_time', models.BigIntegerField(help_text='The time that the event occurred.')),
            ],
        ),
    ]
