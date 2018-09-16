from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'mainapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('createtopic/', views.CreateTopic.as_view(), name='create_topic'),
    path('topics/<str:topic_name>/', views.ChatView.as_view(), name='chat_room'),
    path('topics/<str:topic_name>/chat/archive/', views.ChatArchive.as_view(), name='chat_archive'),
    path('topics/<str:topic_name>/forum/', views.TopicForum.as_view(), name='topic_forum'),
    path('topics/<str:topic_name>/forum/<int:pk>/<slug:slug>/', views.ViewPost.as_view(), name='view_post'),
    path('topicslist/', views.TopicsList.as_view(), name='topics_list'),
    path('search/', views.SearchView.as_view(), name='search_view'),
    path('chatsubscription/', views.ChatRoomSubscription.as_view(), name='chat_subscription'),
    path('topics/<str:topic_name>/forum/create_post', views.CreateTopicPost.as_view(), name='create_topic_post'),
    path('forum/addcomment/<int:pk>/', views.ForumAddComment.as_view(), name='forum_add_comment'),
    path('forum/votecomment/<int:pk>/', views.VoteCommentView.as_view(), name='vote_comment'),
    path('forum/deletecomment/<int:pk>/', views.DeleteCommentView.as_view(), name='delete_comment'),
    path('forum/editcomment/<int:pk>/', views.EditCommentView.as_view(), name='edit_comment'),
    path('forum/votepost/<int:pk>/', views.VotePostView.as_view(), name='vote_post'),
]