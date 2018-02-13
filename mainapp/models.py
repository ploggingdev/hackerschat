from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify

class Topic(models.Model):
    """
    Model representing the topics. Eg-python, android
    """

    #Fields
    name = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^[a-z]+$', "Only lower case letters without spaces are allowed")])
    title = models.CharField(max_length=25, null=True, blank=True ,validators=[RegexValidator(r'^[a-zA-Z0-9 ]+$', "Only lower case, upper case letters, numbers and spaces are allowed")])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String to represent the topic name
        """

        return self.title

class ChatMessage(models.Model):
    """
    Model to represent user submitted changed to a resource guide
    """

    #Fields
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=3000)
    message_html = models.TextField()
    toxicity_score = models.FloatField(default=0.0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String to represent the message
        """

        return self.topic.name + " message"