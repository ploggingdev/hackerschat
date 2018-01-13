from channels import Group
from channels.sessions import channel_session
from .models import Topic, ChatMessage
from django.contrib.auth.models import User
import json
from channels.auth import channel_session_user, channel_session_user_from_http
from django.utils.html import escape
from django.core import serializers
import markdown
import bleach
import re
from django.conf import settings
from django.urls import reverse
import time, datetime
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

@channel_session_user_from_http
def chat_connect(message, topic_name):
    try:
        topic = Topic.objects.get(name=topic_name)
    except ObjectDoesNotExist:
        message.reply_channel.send({"close": True})
        return
    Group(topic_name).add(message.reply_channel)
    user_info = {'last_seen' : time.time(), 'reply_channel' : message.reply_channel.name, 'topic' : topic_name}
    #update user_list in redis
    if message.user.is_authenticated:
        user_info['username'] = message.user.username
    else:
        user_info['username'] = None

    user_list = cache.get('user_list')
    if user_list == None:
        user_list = list()
        user_list.append(user_info)
        cache.set('user_list', user_list)
    else:
        user_updated = False
        for item in user_list:
            if item['reply_channel'] == user_info['reply_channel']:
                user_list.remove(item)
                user_list.append(user_info)
                user_updated = True
        if not user_updated:
            user_list.append(user_info)
        cache.set('user_list', user_list)
    message.reply_channel.send({"accept": True})
    #send presence info to user
    topic_users = cache.get('topic_users')
    topic_anon_count = cache.get('topic_anon_count')
    if topic_users == None or topic_anon_count == None or topic_name not in topic_users or topic_name not in topic_anon_count:
        return
    message.reply_channel.send({
        'text': json.dumps({
            'type': 'presence',
            'payload': {
                'channel_name': topic_name,
                'members': list(topic_users[topic_name]),
                'lurkers': topic_anon_count[topic_name],
            }
        })
    })

@channel_session_user
def chat_receive(message, topic_name):
    try:
        topic = Topic.objects.get(name=topic_name)
    except ObjectDoesNotExist:
        return
    #check for hearbeat
    if message.content.get('text') == '"heartbeat"':
        user_info = {'last_seen' : time.time(), 'reply_channel' : message.reply_channel.name, 'topic' : topic_name}
        #add to redis
        if message.user.is_authenticated:
            user_info['username'] = message.user.username
        else:
            user_info['username'] = None
        user_list = cache.get('user_list')
        if user_list != None:
            user_updated = False
            for item in user_list:
                if item['reply_channel'] == user_info['reply_channel']:
                    user_list.remove(item)
                    item['last_seen'] = time.time()
                    user_list.append(item)
                    cache.set('user_list', user_list)
                    user_updated = True
            if not user_updated:
                user_list.append(user_info)
                cache.set('user_list', user_list)
        return
    #ignore message if user is not authenticated
    if not message.user.is_authenticated:
        return
    #check if rate limit has been reached
    if ChatMessage.objects.filter(user=message.user).filter(created__gte=timezone.now() - datetime.timedelta(minutes=1)).count() >=5:
        message.reply_channel.send({
            'text': json.dumps({
                'type': 'error',
                'payload': {
                    'message': "Rate limit reached. You can send 5 messages per minute.",
                }
            })
        })
        return

    data = json.loads(message['text'])
    if not data['message']:
        return
    
    current_message = escape(data['message'])
    urlRegex = re.compile(
            u'(?isu)(\\b(?:https?://|www\\d{0,3}[.]|[a-z0-9.\\-]+[.][a-z]{2,4}/)[^\\s()<'
            u'>\\[\\]]+[^\\s`!()\\[\\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019])'
        )
    
    processed_urls = list()
    for obj in urlRegex.finditer(current_message):
        old_url = obj.group(0)
        if old_url in processed_urls:
            continue
        processed_urls.append(old_url)
        new_url = old_url
        if not old_url.startswith(('http://', 'https://')):
            new_url = 'http://' + new_url
        new_url = '<a href="' + new_url + '" rel="noopener noreferrer nofollow" target="_blank">' + new_url + "</a>"
        current_message = current_message.replace(old_url, new_url)
    m = ChatMessage(user=message.user,topic=topic, message=data['message'], message_html=current_message)
    m.save()

    user_profile_url = reverse('user_auth:public_user_profile', args=[m.user.username])

    my_dict = {'user' : m.user.username, 'message' : current_message, 'user_profile_url' : user_profile_url}
    Group(topic_name).send({'text': json.dumps(my_dict)})

@channel_session_user
def chat_disconnect(message, topic_name):
    try:
        topic = Topic.objects.get(name=topic_name)
    except ObjectDoesNotExist:
        return
    Group(topic_name).discard(message.reply_channel)
    user_info = {'last_seen' : time.time(), 'reply_channel' : message.reply_channel.name, 'topic' : topic_name}
    #remove from redis
    user_list = cache.get('user_list')
    if user_list != None:
        for item in user_list:
            if item['reply_channel'] == user_info['reply_channel']:
                user_list.remove(item)
        cache.set('user_list', user_list)

@channel_session_user_from_http
def scrollback_connect(message, topic_name):
    try:
        topic = Topic.objects.get(name=topic_name)
    except ObjectDoesNotExist:
        message.reply_channel.send({"close": True})
        return
    message.reply_channel.send({"accept": True})

@channel_session_user
def scrollback_receive(message, topic_name):
    try:
        topic = Topic.objects.get(name=topic_name)
    except ObjectDoesNotExist:
        return
    data = json.loads(message['text'])
    chat_queryset = ChatMessage.objects.filter(topic=topic).filter(id__lte=data['last_message_id']).order_by("-created")[:10]
    chat_message_count = len(chat_queryset)
    if chat_message_count > 0:
        first_message_id = chat_queryset[len(chat_queryset)-1].id
    else:
        first_message_id = -1
    previous_id = -1
    if first_message_id != -1:
        try:
            previous_id = ChatMessage.objects.filter(topic=topic).filter(pk__lt=first_message_id).order_by("-pk")[:1][0].id
        except IndexError:
            previous_id = -1

    chat_messages = reversed(chat_queryset)
    cleaned_chat_messages = list()
    for item in chat_messages:
        current_message = item.message_html
        user_profile_url = reverse('user_auth:public_user_profile', args=[item.user.username])
        cleaned_item = {'user' : item.user.username, 'message' : current_message, 'user_profile_url' : user_profile_url}
        cleaned_chat_messages.append(cleaned_item)

    my_dict = { 'messages' : cleaned_chat_messages, 'previous_id' : previous_id }
    message.reply_channel.send({'text': json.dumps(my_dict)})

@channel_session_user
def scrollback_disconnect(message, topic_name):
    pass