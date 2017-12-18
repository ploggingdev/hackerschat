from django.contrib import admin
from .models import Topic, ChatMessage
from .forms import AdminChatMessageForm, AdminTopicForm
from reversion.admin import VersionAdmin

@admin.register(Topic)
class TopicAdmin(VersionAdmin):
    form = AdminTopicForm
    list_display = ('name','updated','created')

@admin.register(ChatMessage)
class ChatMessageAdmin(VersionAdmin):
    form = AdminChatMessageForm
    list_display = ('user','topic','updated','created')
    list_filter = ['topic']