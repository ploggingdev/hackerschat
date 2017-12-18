from django import forms
from django.forms import ModelForm
from .models import Topic, ChatMessage
import bleach
import markdown
from django.conf import settings
from django.utils.html import escape
import re

class AdminTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'title']

class AdminChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['topic', 'user', 'message', 'message_html']

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