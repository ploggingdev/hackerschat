from django import template
from mainapp.models import Subscription
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def subscription_text(topic, username):
    user = User.objects.get(username=username)
    try:
        subscription = Subscription.objects.get(topic=topic, user=user)
        if subscription.deleted:
            return "Subscribe"
        else:
            return "Unsubscribe"
    except ObjectDoesNotExist:
        return "Subscribe"