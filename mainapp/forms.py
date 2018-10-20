from django import forms
from django.forms import ModelForm
from .models import Topic, ChatMessage, Subscription, Comment, Post, Room
import bleach
import markdown
from django.conf import settings
from django.utils.html import escape
import re
from django.core.validators import RegexValidator

class CreateRoomForm(forms.Form):
    name = forms.CharField(max_length=20, validators=[RegexValidator(r'^[a-z]+$', "Only lower case letters without spaces are allowed")])

class AdminTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'title']

class AdminRoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'topic', 'position']

class AdminChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['topic', 'room', 'user', 'message', 'message_html']

    def clean(self):
        message = self.cleaned_data['message']

        message_html = escape(message)
        urlRegex = re.compile(
            u'(?isu)(\\b(?:https?://|www\\d{0,3}[.]|[a-z0-9.\\-]+[.][a-z]{2,4}/)[^\\s()<'
            u'>\\[\\]]+[^\\s`!()\\[\\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019])'
        )
        
        processed_urls = list()
        for obj in urlRegex.finditer(message_html):
            old_url = obj.group(0)
            if old_url in processed_urls:
                continue
            processed_urls.append(old_url)
            new_url = old_url
            if not old_url.startswith(('http://', 'https://')):
                new_url = 'http://' + new_url
            new_url = '<a href="' + new_url + '">' + new_url + "</a>"
            message_html = message_html.replace(old_url, new_url)

        self.cleaned_data['message_html'] = message_html

        return self.cleaned_data

class AdminSubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['topic', 'user', 'deleted']

class AdminCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment_text', 'comment_text_html', 'post', 'parent', 'user', 'deleted', 'upvotes', 'downvotes', 'net_votes']

    def clean(self):
        if self.cleaned_data['parent']:
            if self.cleaned_data['parent'].post != self.cleaned_data['post']:
                raise forms.ValidationError("The parent comment chosen does not belong to the selected post.")
        comment_text = self.cleaned_data['comment_text']

        comment_text_html = markdown.markdown(comment_text)
        comment_text_html = bleach.clean(comment_text_html, tags=settings.COMMENT_TAGS, strip=True)
        soup = BeautifulSoup(comment_text_html, "html.parser")
        for i in soup.find_all('a'):
            i['target'] = '_blank'
        for i in soup.find_all('blockquote'):
            i['class'] = 'blockquote'
        comment_text_html = soup.prettify()

        self.cleaned_data['comment_text_html'] = comment_text_html

        return self.cleaned_data

class AdminPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['topic', 'title','url','body', 'body_html', 'user', 'deleted', 'upvotes', 'rank']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }

    def clean(self):
        body = self.cleaned_data['body']
        url = self.cleaned_data['url']
        if body and url:
            raise forms.ValidationError("Submit either a url or the body, but not both.")
        if not body and not url:
            raise forms.ValidationError("Submit either a url or the body. Atleast one of the fields has to entered.")
        if body:
            body_html = markdown.markdown(body)
            body_html = bleach.clean(body_html, tags=settings.POST_TAGS, strip=True)
        else:
            body = None
            body_html = None

        self.cleaned_data['body_html'] = body_html

        return self.cleaned_data

class PostModelForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'url', 'body']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 12}),
        }

class CommentForm(forms.Form):
    comment = forms.CharField(label='Comment', max_length=2000, widget=forms.Textarea)
    parent_id = forms.CharField(widget=forms.HiddenInput(), initial="None")

class CommentEditForm(forms.Form):
    comment = forms.CharField(label='Comment', max_length=2000, widget=forms.Textarea)
    comment_id = forms.CharField(widget=forms.HiddenInput())