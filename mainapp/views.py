from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .models import Topic, ChatMessage
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import datetime
from django.utils import timezone
from django.urls import reverse

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
        chat_queryset = ChatMessage.objects.filter(topic=topic).order_by("-created")[:30]
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

class ChatArchive(View):
    template_name = 'mainapp/chat_archive.html'

    def get(self, request, topic_name):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        first_message = ChatMessage.objects.earliest('created')
        now = timezone.now()
        min_date = datetime.datetime(first_message.created.year, first_message.created.month, first_message.created.day, tzinfo=now.tzinfo)
        given_date = request.GET.get('date', None)
        error_message = None
        if given_date == None:
            given_date = datetime.datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
        else:
            try:
                #hacky way to set timezone to utc
                given_date = datetime.datetime.strptime(given_date, "%Y-%m-%d")
                given_date = datetime.datetime(given_date.year, given_date.month, given_date.day, tzinfo=now.tzinfo)
                if given_date < min_date or now < given_date:
                    error_message = "Invalid date selected."
            except ValueError:
                error_message = "Invalid date selected."
        message = "Choose a date between {} and {} to view the chat archive:".format(min_date.strftime('%b-%d-%Y'), now.strftime('%b-%d-%Y'))
        if error_message != None:
            return render(request, self.template_name, {'topic' : topic, 'error_message' : error_message, 'message' : message})
        chat_messages = ChatMessage.objects.filter(created__gte=given_date).filter(created__lte=given_date + datetime.timedelta(days=1))
        # next/prev links
        if given_date - datetime.timedelta(days=1) < min_date:
            prev_page = None
        else:
            prev_page = "{}?date={}".format(reverse('mainapp:chat_archive', args=[topic_name,]), (given_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        if now < given_date + datetime.timedelta(days=1):
            next_page = None
        else:
            next_page = "{}?date={}".format(reverse('mainapp:chat_archive', args=[topic_name,]), (given_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        #format date
        given_date = given_date.strftime('%b-%d-%Y')
        return render(request, self.template_name, {'topic' : topic, 'chat_messages' : chat_messages, 'date' : given_date, 'error_message' : error_message, 'message' : message, 'prev_page' : prev_page, 'next_page' : next_page})