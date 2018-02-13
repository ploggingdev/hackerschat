from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

class Topic(models.Model):

    name = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^[a-z]+$', "Only lower case letters without spaces are allowed")])
    title = models.CharField(max_length=25, null=True, blank=True ,validators=[RegexValidator(r'^[a-zA-Z0-9 ]+$', "Only lower case, upper case letters, numbers and spaces are allowed")])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ChatMessage(models.Model):

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=3000)
    message_html = models.TextField()
    toxicity_score = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.topic.name + " message"

class Subscription(models.Model):

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}-{}".format(self.topic, self.user)