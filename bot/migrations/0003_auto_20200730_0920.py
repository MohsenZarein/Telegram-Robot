# Generated by Django 2.2.1 on 2020-07-30 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0002_auto_20200729_1155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='members',
            name='member_access_hash',
            field=models.CharField(max_length=500),
        ),
    ]