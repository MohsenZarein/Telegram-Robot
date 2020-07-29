from django.db import models
from django.contrib.postgres.fields import ArrayField

class Target_Groups(models.Model):

    link = models.CharField(max_length=200)

    def __str__(self):
        return self.link


class Source_Groups(models.Model):

    link = models.CharField(max_length=200)

    def __str__(self):
        return self.link
    

class Members(models.Model):

    member_id = models.CharField(max_length=100)
    member_access_hash = models.CharField(max_length=200)
    member_username = models.CharField(max_length=100)
    member_joined_groups = ArrayField(models.CharField(max_length=200) , blank=True , default=list)

    def __str__(self):
        return self.member_id


class Workers(models.Model):

    worker_api_id = models.CharField(max_length=100)
    worker_api_hash = models.CharField(max_length=200)
    worker_phone = models.CharField(max_length=50)
    limited = models.BooleanField(default=False)

    def __str__(self):
        return self.worker_phone