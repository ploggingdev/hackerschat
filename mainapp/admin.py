from django.contrib import admin
from .models import Topic, ChatMessage, Subscription, Comment, VoteComment, Post, VotePost, Room
from .forms import AdminChatMessageForm, AdminTopicForm, AdminSubscriptionForm, AdminCommentForm, AdminPostForm, AdminRoomForm
from reversion.admin import VersionAdmin
from mptt.admin import MPTTModelAdmin

@admin.register(Topic)
class TopicAdmin(VersionAdmin):
    form = AdminTopicForm
    list_display = ('name','updated','created')

@admin.register(Room)
class RoomAdmin(VersionAdmin):
    form = AdminRoomForm
    list_display = ('name', 'topic','updated','created')

@admin.register(ChatMessage)
class ChatMessageAdmin(VersionAdmin):
    form = AdminChatMessageForm
    list_display = ('user','toxicity_score','topic','updated','created')
    list_filter = ['topic']

@admin.register(Subscription)
class SubscriptionAdmin(VersionAdmin):
    form = AdminSubscriptionForm
    list_display = ('topic', 'user', 'deleted', 'updated', 'created')

@admin.register(Comment)
class CommentAdmin(MPTTModelAdmin):
    form = AdminCommentForm
    list_display = ('comment_text','user' ,'created', 'net_votes')

@admin.register(VoteComment)
class VoteCommentAdmin(VersionAdmin):
    list_display = ('user', 'value' ,'created')

@admin.register(VotePost)
class VotePostAdmin(VersionAdmin):
    list_display = ('user', 'value' ,'created')

@admin.register(Post)
class PostAdmin(VersionAdmin):
    form = AdminPostForm
    list_display = ('title','body', 'deleted','user','created')