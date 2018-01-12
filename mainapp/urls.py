from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'mainapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('topics/<str:topic_name>/chat/archive/', views.ChatArchive.as_view(), name='chat_archive'),
]