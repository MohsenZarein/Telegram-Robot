# Generated by Django 2.2.1 on 2020-07-29 11:55

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='members',
            name='member_joined_groups',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, default=list, size=None),
        ),
        migrations.AddField(
            model_name='workers',
            name='limited',
            field=models.BooleanField(default=False),
        ),
    ]
