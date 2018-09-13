from __future__ import absolute_import, unicode_literals
import os
from celery import Celery, shared_task
from django.core.cache import cache
from django.conf import settings
import json
import time
import requests
from django.core.exceptions import ObjectDoesNotExist
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hackerschat.settings')

app = Celery('hackerschat', broker=os.environ['redis_url'])

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(settings.CELERY_TASK_INTERVAL, broadcast_presence.s(), name="Broadcast presence", expires=settings.CELERY_TASK_EXPIRES)
    sender.add_periodic_task(60.0, update_rank.s(), name="Update rank", expires=10)

@app.task
def update_rank():
    from mainapp.models import Post, Comment
    from django.db.models import Count
    from django.utils import timezone
    import datetime
    posts = Post.objects.filter(deleted=False).annotate(comments_count=Count('comment')).filter(created__gte=timezone.now() - datetime.timedelta(days=3))
    for post in posts:
        post.calculate_rank(post.comments_count)

@app.task(time_limit=10)
def prune_redis_user_list():
    user_list = cache.get('user_list')
    if user_list == None:
        user_list = list()
        cache.set('user_list', user_list)
    else:
        for item in user_list:
            if time.time() - item['last_seen'] > settings.LAST_SEEN_LIMIT :
                user_list.remove(item)
        cache.set('user_list', user_list)

@app.task(time_limit=20)
def broadcast_presence():
    channel_layer = get_channel_layer()
    prune_redis_user_list()
    update_presence_data()
    user_list = cache.get('user_list')
    topic_users = cache.get('topic_users')
    topic_anon_count = cache.get('topic_anon_count')
    topics = cache.get('topics')
    for topic_name in topics:
        async_to_sync(channel_layer.group_send)(
            topic_name,
            {
                "type": "presence.data",
                'payload': {
                    'channel_name': topic_name,
                    'members': list(topic_users[topic_name]),
                    'lurkers': topic_anon_count[topic_name],
                }
            },
        )

@app.task(time_limit=10)
def update_presence_data():
    user_list = cache.get('user_list')
    if user_list == None:
        user_list = list()
        cache.set('user_list', user_list)
    topic_users = {}
    topic_anon_count = {}
    topics = set()
    for user in user_list:
        topic_name = user['topic']
        topics.add(topic_name)
        if topic_name not in topic_users:
            topic_users[topic_name] = set()
        if user['username'] != None:
            topic_users[topic_name].add(user['username'])

        if topic_name not in topic_anon_count:
            topic_anon_count[topic_name] = 0
        if user['username'] == None:
            topic_anon_count[topic_name] += 1
    cache.set('topic_users', topic_users)
    cache.set('topic_anon_count', topic_anon_count)
    cache.set('topics', topics)

@app.task(time_limit=10)
def check_message_toxicity(message_id):
    from mainapp.models import ChatMessage
    from django.utils import timezone
    from django.core.mail import send_mail
    import datetime
    try:
        message = ChatMessage.objects.get(pk=message_id)
    except ObjectDoesNotExist:
        return
    request_data = {"comment": {"text": message.message},"languages": ["en"],"requestedAttributes": {"TOXICITY":{}} }
    try:
        r = requests.post(settings.TOXICITY_ENDPOINT, json=request_data)
        r.raise_for_status()
    except:
        return
    if r.status_code == 200:
        try:
            json_response = r.json()
            toxicity_score = json_response['attributeScores']['TOXICITY']['summaryScore']['value']
            if isinstance(toxicity_score, float):
                message.toxicity_score = toxicity_score
                if toxicity_score > 0.9:
                    if not message.user.userprofile.to_review:
                        message.user.userprofile.to_review = True
                        message.user.userprofile.save()
                    if not message.user.is_superuser and message.user.is_active and ChatMessage.objects.filter(user=message.user).filter(created__gte=timezone.now() - datetime.timedelta(days=1)).filter(toxicity_score__gte=0.9).count() >= 10:
                        message.user.is_active = False
                        message.user.save()
                        send_mail(
                        'User {} banned'.format(message.user),
                        'Username : {}'.format(message.user),
                        'hackerschat@ploggingdev.com',
                        ['ploggingdev@gmail.com'],
                        fail_silently=False,
                        )
                message.save()
        except:
            #to add logging
            pass