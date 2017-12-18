from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .models import Topic, ChatMessage

class IndexView(View):
    template_name = 'mainapp/home_page.html'

    def get(self, request):
        """
        Chat room
        """

        # hardcoded topic name initially
        name = "general"
        topic = Topic.objects.get(name=name)

        # We want to show the last 10 messages, ordered most-recent-last
        chat_queryset = ChatMessage.objects.filter(topic=topic).order_by("-created")[:10]
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
        
        return render(request, self.template_name, {
            'topic': topic,
            'chat_messages': chat_messages,
            'first_message_id' : previous_id
        })

class AboutView(View):
    template_name = 'mainapp/about.html'

    def get(self, request):
        return render(request, self.template_name)