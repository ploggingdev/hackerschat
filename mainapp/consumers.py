from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Topic, ChatMessage
from django.contrib.auth.models import User
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
from hackerschat import celery

class ChatConsumer(JsonWebsocketConsumer):

    def connect(self):
        topic_name = self.scope['url_route']['kwargs']['topic_name']
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            self.close()
            return
        async_to_sync(self.channel_layer.group_add)(topic_name, self.channel_name)
        user_info = {'last_seen' : time.time(), 'reply_channel' : self.channel_name, 'topic' : topic_name}
        #update user_list in redis
        if self.scope["user"].is_authenticated:
            user_info['username'] = self.scope["user"].username
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
        self.accept()
        #send presence info to user
        topic_users = cache.get('topic_users')
        topic_anon_count = cache.get('topic_anon_count')
        if topic_users == None or topic_anon_count == None or topic_name not in topic_users or topic_name not in topic_anon_count:
            return
        self.send_json(
            {
                'message_type': 'presence',
                'payload': {
                    'channel_name': topic_name,
                    'members': list(topic_users[topic_name]),
                    'lurkers': topic_anon_count[topic_name],
                }
            }
        )

    def receive_json(self, content):
        topic_name = self.scope['url_route']['kwargs']['topic_name']
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            return
        if type(content) is not dict:
            return
        message = content.get('message', None)
        heartbeat = content.get('heartbeat', None)
        last_message_id = content.get('last_message_id', None)
        if message == None and heartbeat == None and last_message_id == None:
            return
        #heartbeat
        if heartbeat:
            self.heartbeat(topic_name)
            return
        #scrollback
        if last_message_id:
            self.scrollback(topic, last_message_id)
            return
        #chat message
        if message:
            self.handle_chat_message(message, topic)

    def disconnect(self, code):
        topic_name = self.scope['url_route']['kwargs']['topic_name']
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            return
        async_to_sync(self.channel_layer.group_discard)(topic_name, self.channel_name)
        user_info = {'last_seen' : time.time(), 'reply_channel' : self.channel_name, 'topic' : topic_name}
        #remove from redis
        user_list = cache.get('user_list')
        if user_list != None:
            for item in user_list:
                if item['reply_channel'] == user_info['reply_channel']:
                    user_list.remove(item)
            cache.set('user_list', user_list)
    
    def heartbeat(self, topic_name):
        user_info = {'last_seen' : time.time(), 'reply_channel' : self.channel_name, 'topic' : topic_name}
        #add to redis
        if self.scope["user"].is_authenticated:
            user_info['username'] = self.scope["user"].username
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
    
    def scrollback(self, topic, last_message_id):
        try:
            last_message_id = int(last_message_id)
        except ValueError:
            return
        chat_queryset = ChatMessage.objects.filter(topic=topic).filter(id__lte=last_message_id).order_by("-created")[:10]
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
        self.send_json(
            {
                'message_type' : 'scrollback',
                'messages' : cleaned_chat_messages,
                'previous_id' : previous_id,
            },
        )
    
    def handle_chat_message(self, message, topic):
        if len(message) > 1500:
            self.send_json({
                'type': 'error',
                'payload': {
                    'message': "Maximum message size is 1500 characters.",
                }
            })
            return
        topic_name = topic.name
        #ignore message if user is not authenticated
        if not self.scope["user"].is_authenticated or not message:
            return
        #check if rate limit has been reached
        if ChatMessage.objects.filter(user=self.scope["user"]).filter(created__gte=timezone.now() - datetime.timedelta(minutes=1)).count() >= 10:
            self.send_json({
                    'type': 'error',
                    'payload': {
                        'message': "Rate limit reached. You can send 10 messages per minute.",
                    }
            })
            return
        
        current_message = escape(message)
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

        m = ChatMessage(user=self.scope["user"],topic=topic, message=message, message_html=current_message)
        m.save()
        celery.check_message_toxicity.delay(m.id)

        user_profile_url = reverse('user_auth:public_user_profile', args=[m.user.username])

        my_dict = {'user' : m.user.username, 'message' : current_message, 'user_profile_url' : user_profile_url}
        async_to_sync(self.channel_layer.group_send)(
            topic_name,
            {
                "type": "group.message",
                'user' : m.user.username,
                'message' : current_message,
                'user_profile_url' : user_profile_url
            },
        )
    
    def group_message(self, event):
        self.send_json({
            'user' : event['user'],
            'message' : event['message'],
            'user_profile_url' : event['user_profile_url']
        })
    
    def presence_data(self, event):
        self.send_json({
            'message_type': 'presence',
            'payload': event['payload']
        })