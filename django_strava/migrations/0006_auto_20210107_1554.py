# Generated by Django 3.1.5 on 2021-01-07 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('strava', '0005_auto_20210107_1540'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stravaathlete',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='strava.stravatoken'),
        ),
    ]
