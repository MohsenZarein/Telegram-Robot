# Generated by Django 2.2.1 on 2020-08-09 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_auto_20200801_1957'),
    ]

    operations = [
        migrations.AddField(
            model_name='members',
            name='member_source_group',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
