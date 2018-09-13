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

@register.filter
def get_post_vote_value(user_votes, post_id):
    for vote in user_votes:
        if vote.post.id == post_id:
            return vote.value
    return 0

@register.filter
def get_comments(val):
    if val == 1:
        return "comment"
    else:
        return "comments"