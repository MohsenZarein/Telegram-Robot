from django.db import models

class Target_Groups(models.Model):
    link = models.CharField(max_length=200)


class Source_Groups(models.Model):
    link = models.CharField(max_length=200)
    

class Members(models.Model):
    member_id = models.CharField(max_length=100)
    member_access_hash = models.CharField(max_length=200)
    member_username = models.CharField(max_length=100)


class Workers(models.Model):
    worker_api_id = models.CharField(max_length=100)
    worker_api_hash = models.CharField(max_length=200)
    worker_phone = models.CharField(max_length=50) 