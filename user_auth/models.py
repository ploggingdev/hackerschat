from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.CharField(max_length=1000, default="[empty]")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)