from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .models import Topic, ChatMessage, Subscription
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse
import datetime
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from mainapp.forms import CreateRoomForm
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
        #subscribed rooms
        subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        return render(request, self.template_name, {
            'topic': topic,
            'chat_messages': chat_messages,
            'first_message_id' : previous_id,
            'subscribed_rooms' : subscribed_rooms
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
        first_message = ChatMessage.objects.filter(topic=topic).earliest('created')
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
        chat_messages = ChatMessage.objects.filter(topic=topic).filter(created__gte=given_date).filter(created__lte=given_date + datetime.timedelta(days=1)).order_by('created')
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

class ChatView(View):
    template_name = 'mainapp/chat_room.html'

    def get(self, request, topic_name):
        """
        Chat room
        """

        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")

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
        #subscribed rooms
        subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        return render(request, self.template_name, {
            'topic': topic,
            'chat_messages': chat_messages,
            'first_message_id' : previous_id,
            'subscribed_rooms' : subscribed_rooms
        })

class CreateRoom(LoginRequiredMixin, View):
    form_class = CreateRoomForm
    template_name = "mainapp/create_room.html"

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form' : form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            topic_name = form.cleaned_data['name']
            topic_count = Topic.objects.filter(name=topic_name).count()
            if topic_count == 0:
                topic = Topic(name=topic_name, title=topic_name)
                topic.save()
                messages.success(request ,"Room has been created successfully")
                return redirect(reverse("mainapp:chat_room", args=[topic_name]))
            else:
                messages.error(request ,"Topic already exists")
                return redirect(reverse("mainapp:chat_room", args=[topic_name]))
        else:
            messages.error(request, "Invalid form data. Only lower case letters are allowed.")
            return render(request, self.template_name, {'form' : self.form_class()})

class RoomsList(View):
    template_name = "mainapp/rooms_list.html"
    paginate_by = 10

    def get(self, request):
        rooms = Topic.objects.all().order_by('-created')

        paginator = Paginator(rooms, self.paginate_by)

        page = request.GET.get('page', 1)
        try:
            current_page_rooms = paginator.page(page)
        except PageNotAnInteger:
            messages.error(request, "Invalid page number, showing the first page instead.")
            current_page_rooms = paginator.page(1)
        except EmptyPage:
            messages.error(request, "Invalid page number, showing the last page instead.")
            current_page_rooms = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'current_page_rooms': current_page_rooms})

class SearchView(View):
    template_name = "mainapp/search.html"
    paginate_by = 10

    def get(self, request):
        search_query = request.GET.get('query', None)
        if search_query == None or len(search_query) > 20:
            messages.error(request, "Invalid search query")
            return render(request, self.template_name, {'current_page_rooms': None, search_query : None})

        rooms = Topic.objects.filter(name__trigram_similar=search_query.lower()) | Topic.objects.filter(name__icontains=search_query.lower())

        paginator = Paginator(rooms, self.paginate_by)

        page = request.GET.get('page', 1)
        try:
            current_page_rooms = paginator.page(page)
        except PageNotAnInteger:
            messages.error(request, "Invalid page number, showing the first page instead.")
            current_page_rooms = paginator.page(1)
        except EmptyPage:
            messages.error(request, "Invalid page number, showing the last page instead.")
            current_page_rooms = paginator.page(paginator.num_pages)

        return render(request, self.template_name, {'current_page_rooms': current_page_rooms, 'search_query' : search_query })

class ChatRoomSubscription(View):

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error' : 'Please login to subscribe.' }, status=400)

        topic_name = request.POST.get('topic_name', None)
        if topic_name == None:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)

        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            return JsonResponse({'error' : 'Invalid request.' }, status=404)
        
        user = request.user

        try:
            subscription = Subscription.objects.get(topic=topic, user=user)
            if subscription.deleted:
                subscription.deleted = False
                message = "You have subscribed to {}".format(topic.name)
                button_text = "Unsubscribe"
            else:
                subscription.deleted = True
                message = "You have unsubscribed from {}".format(topic.name)
                button_text = "Subscribe"
            subscription.save()
        except ObjectDoesNotExist:
            subscription = Subscription(topic=topic, user=user)
            subscription.save()
            message = "You have subscribed to {}".format(topic.name)
            button_text = "Unsubscribe"
        
        return JsonResponse({'message' : message, 'button_text' : button_text })