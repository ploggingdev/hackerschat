from django.contrib import admin
from .models import Topic, ChatMessage, Subscription
from .forms import AdminChatMessageForm, AdminTopicForm, AdminSubscriptionForm
from reversion.admin import VersionAdmin

@admin.register(Topic)
class TopicAdmin(VersionAdmin):
    form = AdminTopicForm
    list_display = ('name','updated','created')

@admin.register(ChatMessage)
class ChatMessageAdmin(VersionAdmin):
    form = AdminChatMessageForm
    list_display = ('user','toxicity_score','topic','updated','created')
    list_filter = ['topic']

@admin.register(Subscription)
class SubscriptionAdmin(VersionAdmin):
    form = AdminSubscriptionForm
    list_display = ('topic', 'user', 'deleted', 'updated', 'created')