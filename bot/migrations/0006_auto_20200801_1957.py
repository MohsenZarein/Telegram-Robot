# Generated by Django 2.2.1 on 2020-08-01 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_members_adding_permision'),
    ]

    operations = [
        migrations.AlterField(
            model_name='members',
            name='member_username',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]