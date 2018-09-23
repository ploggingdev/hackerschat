from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from .models import Topic, ChatMessage, Subscription, Post, VotePost, Comment, VoteComment
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse, HttpResponseBadRequest
import datetime
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from mainapp.forms import CreateRoomForm, PostModelForm, CommentForm, CommentEditForm
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db.models import Count, Q
import markdown
import bleach
from bs4 import BeautifulSoup
from itertools import chain
from django.contrib.auth.models import User
from operator import attrgetter

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
        if request.user.is_authenticated:
            subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        else:
            subscribed_rooms = None
        return render(request, self.template_name, {
            'topic': topic,
            'chat_messages': chat_messages,
            'first_message_id' : previous_id,
            'subscribed_rooms' : subscribed_rooms,
            'default_rooms' : settings.DEFAULT_TOPICS
        })

class AboutView(View):
    template_name = 'mainapp/about.html'

    def get(self, request):
        return render(request, self.template_name)

class TopicForum(View):
    paginate_by = 10
    template_name = 'mainapp/topic_forum.html'

    def get(self, request, topic_name):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        comments_count = Count('comment', filter=Q(comment__deleted=False))
        if request.GET.get('sort_by') == "new":
            all_results = Post.objects.filter(topic=topic).filter(deleted=False).order_by('-created').annotate(comments_count=comments_count)
            sort_by = "New"
        else:
            sort_by = "Popular"
            all_results = Post.objects.filter(topic=topic).filter(deleted=False).order_by('-rank').annotate(comments_count=comments_count)

        paginator = Paginator(all_results, self.paginate_by)

        page = request.GET.get('page')
        try:
            post_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            post_list = paginator.page(1)
            page = 1
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            post_list = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        
        if request.user.is_authenticated:
            user_votes = VotePost.objects.filter(user=request.user)
        else:
            user_votes = list()

        #subscribed rooms
        if request.user.is_authenticated:
            subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        else:
            subscribed_rooms = None

        return render(request, self.template_name, {'post_list' : post_list, 'sort_by' : sort_by, 'user_votes' : user_votes, 'topic' : topic, 'page' : page, 'subscribed_rooms' : subscribed_rooms, 'default_rooms' : settings.DEFAULT_TOPICS })

class CreateTopicPost(LoginRequiredMixin, View):
    form_class  = PostModelForm
    template_name = 'mainapp/create_post.html'

    def get(self, request, topic_name):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        form = self.form_class()
        #subscribed rooms
        subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        return render(request, self.template_name, {'form' : form, 'topic' : topic, 'subscribed_rooms' : subscribed_rooms})
    
    def post(self, request, topic_name):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        form = self.form_class(request.POST)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            body = form.cleaned_data['body']
            url = form.cleaned_data['url']

            subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
            if body and url:
                messages.error(request, 'Submit either a url or the body, but not both.')
                return render(request, self.template_name, {'form' : form, 'topic' : topic, 'subscribed_rooms' : subscribed_rooms})
            if not body and not url:
                messages.error(request, 'Submit either a url or the body. Atleast one of the fields has to entered.')
                return render(request, self.template_name, {'form' : form, 'topic' : topic, 'subscribed_rooms' : subscribed_rooms})
            if body:
                body_html = markdown.markdown(body)
                body_html = bleach.clean(body_html, tags=settings.POST_TAGS, strip=True)
            else:
                body = None
                body_html = None
            article = Post(topic=topic, title=title, url=url, body=body, user=request.user, body_html=body_html)

            article.save()
            vote_obj = VotePost(user=request.user,
                                post=article,
                                value=1)
            vote_obj.save()
            article.upvotes += 1
            article.save()
            messages.success(request, 'Post has been submitted.')
            return redirect(reverse('mainapp:topic_forum', args=[topic]) + '?sort_by=new')
        else:
            return render(request, self.template_name, {'form' : form})

class ViewPost(View):
    template_name = 'mainapp/view_post.html'
    form_class = CommentForm

    def get(self, request, topic_name, pk, slug):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        
        try:
            post = Post.objects.get(topic=topic, pk=pk)
        except Post.DoesNotExist:
            return
        if post.deleted:
            return

        nodes = Comment.objects.filter(post=post)
        comments_count = len(Comment.objects.filter(post=post).filter(deleted=False))
        if request.user.is_authenticated:
            user_votes = VoteComment.objects.filter(user=request.user).filter(comment__post=post)
        else:
            user_votes = list()
        form = self.form_class(initial={'parent_id' : 'None'})
        #subscribed rooms
        if request.user.is_authenticated:
            subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        else:
            subscribed_rooms = None
        vote_value = 0
        if request.user.is_authenticated:
            try:
                vote_obj = VotePost.objects.filter(user=request.user).get(post=post)
                vote_value = vote_obj.value
            except ObjectDoesNotExist:
                pass
        return render(request, self.template_name, {'post' : post, 'nodes' : nodes, 'form' : form, 'user_votes' : user_votes, 'comments_count' : comments_count, 'topic' : topic, 'subscribed_rooms' : subscribed_rooms, 'vote_value' : vote_value })

class ForumAddComment(View):

    form_class = CommentForm

    def post(self, request, pk):
        
        if not request.user.is_authenticated:
            return JsonResponse({'error' : 'Please login to comment on this post.' }, status=400)
        try:
            post = Post.objects.filter(deleted=False).get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({'error' : 'Invalid post id.' }, status=400)

        form = self.form_class(request.POST)
        
        if post.deleted:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        if form.is_valid():
            if Comment.objects.filter(user=request.user).filter(created__gte=timezone.now() - datetime.timedelta(minutes=60)).count() >= 5:
                return JsonResponse({'error' : 'Rate limit reached. You\'re posting too fast!' }, status=403)
            comment_parent_id = form.cleaned_data['parent_id']
            if comment_parent_id == "None":
                comment_parent_object = None
            else:
                try:
                    comment_parent_id = int(comment_parent_id)
                    comment_parent_object = Comment.objects.get(pk=comment_parent_id)
                    if comment_parent_object.deleted:
                        return JsonResponse({'error' : 'Invalid request. Cannot reply to deleted comment' }, status=400)
                except (ValueError, Comment.DoesNotExist) :
                    return JsonResponse({'error' : 'Invalid request.' }, status=400)
            
            comment_text = form.cleaned_data['comment']
            comment_text_html = markdown.markdown(comment_text)
            comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
            soup = BeautifulSoup(comment_text_html, "html.parser")
            for i in soup.find_all('a'):
                i['target'] = '_blank'
                i['rel'] = 'noopener noreferrer nofollow'
            for i in soup.find_all('blockquote'):
                i['class'] = 'blockquote'
            comment_text_html = soup.prettify()
            
            comment = Comment(comment_text=comment_text, comment_text_html=comment_text_html, user=request.user, post=post, parent=comment_parent_object)

            comment.save()
            vote_obj = VoteComment(user=request.user,
                                comment=comment,
                                value=1)
            vote_obj.save()
            comment.upvotes += 1
            comment.net_votes += 1
            comment.save()
            #todo : notification
            return JsonResponse({'success' : 'Comment has been saved.', 'comment_id' : comment.id, 'comment_html' : comment.comment_text_html, 'username' : comment.user.username, 'comment_raw' : comment.comment_text })
        else:
            return JsonResponse({'error' : 'Invalid form submission.' }, status=400)

class VoteCommentView(View):

    def post(self, request, pk):

        if not request.user.is_authenticated:
            return JsonResponse({'error' : 'Please login to comment on this post.' }, status=400)
        if request.POST.get('vote_value'):
            try:
                comment = Comment.objects.filter(deleted=False).get(pk=pk)
            except Comment.DoesNotExist:
                return JsonResponse({'error' : 'Invalid request.' }, status=400)
            
            if comment.post.deleted:
                return JsonResponse({'error' : 'Invalid request.' }, status=400)

            vote_value = request.POST.get('vote_value', None)

            try:
                vote_value = int(vote_value)
                if vote_value not in [-1, 1]:
                    return JsonResponse({'error' : 'Invalid request.' }, status=400)

            except (ValueError, TypeError):
                return JsonResponse({'error' : 'Invalid request.' }, status=400)

            try:
                vote_obj = VoteComment.objects.get(comment=comment,user=request.user)

            except ObjectDoesNotExist:
                vote_obj = VoteComment(user=request.user,
                                comment=comment,
                                value=vote_value)
                vote_obj.save()
                if vote_value == 1:
                    vote_diff = 1
                    comment.upvotes += 1
                    comment.net_votes += 1
                elif vote_value == -1:
                    vote_diff = -1
                    comment.downvotes += 1
                    comment.net_votes -= 1
                comment.save()

                if comment.user != request.user:
                    comment.user.userprofile.comment_karma +=  vote_diff
                    comment.user.userprofile.save()

                return JsonResponse({'vote_diff': vote_diff})
            
            if vote_obj.value == vote_value:
                # cancel vote
                vote_diff = vote_obj.unvote(request.user)
                if not vote_diff:
                    return JsonResponse({'error' : 'Invalid request.' }, status=400)
            else:
                # change vote
                vote_diff = vote_obj.change_vote(vote_value, request.user)
                if not vote_diff:
                    return JsonResponse({'error' : 'Invalid request.' }, status=400)
            
            return JsonResponse({'vote_diff': vote_diff})
        else:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)

class DeleteCommentView(View):

    def post(self, request, pk):
        
        if not request.user.is_authenticated:
            return JsonResponse({'error' : 'Please login to comment on this post.' }, status=400)
        
        try:
            post = Post.objects.filter(deleted=False).get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        if post.deleted:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        try:
            comment_id = int(request.POST.get('comment_id', None))
        except (ValueError, TypeError):
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        
        try:
            comment = Comment.objects.get(pk=comment_id)
        except Comment.DoesNotExist:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)

        if comment.user == request.user:
            comment.deleted = True
            comment.save()
            return JsonResponse({'success' : 'Comment has been deleted.' })
        else:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)

class EditCommentView(View):

    form_class = CommentEditForm

    def post(self, request, pk):
        
        if not request.user.is_authenticated:
            return JsonResponse({'error' : 'Please login to comment on this post.' }, status=400)

        form = self.form_class(request.POST)
        
        try:
            post = Post.objects.filter(deleted=False).get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        if post.deleted:
            return JsonResponse({'error' : 'Invalid request.' }, status=400)
        if form.is_valid():
            comment_id = form.cleaned_data['comment_id']
            try:
                comment_id = int(comment_id)
                comment_object = Comment.objects.get(pk=comment_id)
            except (ValueError, Comment.DoesNotExist) :
                return JsonResponse({'error' : 'Invalid request.' }, status=400)
            
            comment_text = form.cleaned_data['comment']
            comment_text_html = markdown.markdown(comment_text)
            comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
            soup = BeautifulSoup(comment_text_html, "html.parser")
            for i in soup.find_all('a'):
                i['target'] = '_blank'
                i['rel'] = 'noopener noreferrer nofollow'
            for i in soup.find_all('blockquote'):
                i['class'] = 'blockquote'
            comment_text_html = soup.prettify()
            
            comment_object.comment_text = comment_text
            comment_object.comment_text_html = comment_text_html

            comment_object.save()
            return JsonResponse({'success' : 'Comment has been updated.', 'comment_id' : comment_object.id, 'comment_html' : comment_object.comment_text_html, 'comment_raw' : comment_object.comment_text })
        else:
            return JsonResponse({'error' : 'Invalid form submission.' }, status=400)

class VotePostView(LoginRequiredMixin, View):

    def post(self, request, pk):
        if request.POST.get('vote_value'):
            try:
                post = Post.objects.filter(deleted=False).get(pk=pk)
            except Post.DoesNotExist:
                return HttpResponseBadRequest()

            vote_value = request.POST.get('vote_value', None)

            try:
                vote_value = int(vote_value)
                if vote_value != 1:
                    raise ValueError("Invalid request")

            except (ValueError, TypeError):
                return HttpResponseBadRequest()

            try:
                vote_obj = VotePost.objects.get(post=post,user=request.user)

            except ObjectDoesNotExist:
                vote_obj = VotePost(user=request.user,
                                post=post,
                                value=vote_value)
                vote_obj.save()
                if vote_value == 1:
                    vote_diff = 1
                    post.upvotes += 1
                elif vote_value == -1:
                    vote_diff = -1
                    post.upvotes -= 1
                post.save()

                if post.user != request.user:
                    post.user.userprofile.submission_karma +=  vote_diff
                    post.user.userprofile.save()

                return JsonResponse({'error'   : None,
                                    'vote_diff': vote_diff})
            
            if vote_obj.value == vote_value:
                # cancel vote
                vote_diff = vote_obj.unvote(request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Something went wrong while canceling the vote')
            else:
                # change vote
                vote_diff = vote_obj.vote(vote_value, request.user)
                if not vote_diff:
                    return HttpResponseBadRequest(
                        'Wrong values for old/new vote combination')
            
            return JsonResponse({'error'   : None,
                         'vote_diff': vote_diff})
        else:
            return HttpResponseBadRequest()

class ChatArchive(View):
    template_name = 'mainapp/chat_archive.html'

    def get(self, request, topic_name):
        try:
            topic = Topic.objects.get(name=topic_name)
        except ObjectDoesNotExist:
            raise Http404("Topic does not exist")
        if ChatMessage.objects.filter(topic=topic).count() == 0:
            return render(request, self.template_name, {'topic' : topic, 'error_message' : "No messages have been sent in this chat room", 'message' : "No valid dates can be selected"})
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
        if request.user.is_authenticated:
            subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        else:
            subscribed_rooms = None
        return render(request, self.template_name, {
            'topic': topic,
            'chat_messages': chat_messages,
            'first_message_id' : previous_id,
            'subscribed_rooms' : subscribed_rooms,
            'default_rooms' : settings.DEFAULT_TOPICS
        })

class CreateTopic(LoginRequiredMixin, View):
    form_class = CreateRoomForm
    template_name = "mainapp/create_topic.html"

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
                subscription = Subscription(user=request.user, topic=topic)
                subscription.save()
                messages.success(request ,"Topic has been created successfully")
                return redirect(reverse("mainapp:chat_room", args=[topic_name]))
            else:
                messages.error(request ,"Topic already exists")
                return redirect(reverse("mainapp:chat_room", args=[topic_name]))
        else:
            messages.error(request, "Invalid form data. Only lower case letters are allowed.")
            return render(request, self.template_name, {'form' : self.form_class()})

class TopicsList(View):
    template_name = "mainapp/topics_list.html"
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

class MyPosts(View):
    
    template_name = 'mainapp/myposts.html'
    paginate_by = 10

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            messages.error(request, "User does not exist")
            return render(request, self.template_name, {'error' : True})
        comments = Comment.objects.all().filter(deleted=False).filter(user=user).order_by('-created')
        posts = Post.objects.all().filter(deleted=False).filter(user=user).order_by('-created')

        total_count = Comment.objects.all().filter(deleted=False).filter(user=user).count() + Post.objects.all().filter(deleted=False).filter(user=user).count()

        all_items = chain(comments, posts)
        all_items = sorted(all_items, key=attrgetter('created'), reverse=True)

        paginator = Paginator(all_items, self.paginate_by)

        page = request.GET.get('page')
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            posts = paginator.page(1)
            page = 1
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            posts = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        return render(request, self.template_name, {'posts': posts, 'page' : page, 'user' : user })

class DeletePost(LoginRequiredMixin, View):
    
    template_name = 'mainapp/post_delete.html'

    def get(self, request, topic_name, pk):
        post = get_object_or_404(Post, pk=pk)
        go_back_url = post.get_post_url()
        if (not post.can_delete()) or (post.user != request.user):
            messages.error(request, 'Invalid request, please try again.')
            return redirect(go_back_url)
        subscribed_rooms = Subscription.objects.filter(user=request.user).filter(deleted=False).order_by('topic__name')
        return render(request, self.template_name, {'post' : post, 'go_back_url' : go_back_url, 'subscribed_rooms' : subscribed_rooms, 'topic' : post.topic})
    
    def post(self, request, topic_name, pk):
        
        post = get_object_or_404(Post, pk=pk)
        if request.POST.get('delete_post'):
            if post.can_delete() and post.user == request.user:
                post.deleted = True
                post.save()
                messages.success(request, 'Post has been deleted.')
            else:
                messages.error(request, 'Post could not be deleted.')
        else:
            messages.error(request, 'Invalid request')
        return redirect(post.topic.get_topic_forum_url())