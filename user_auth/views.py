from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, ProfileForm
from django.contrib.auth.models import User
from django.contrib.auth import views, authenticate, login, get_user_model
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core import exceptions
from .models import UserProfile
from django.utils.http import is_safe_url
from django.conf import settings
import requests
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from mainapp.models import Topic, Subscription

class CustomPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        #recaptcha validation
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if recaptcha_response == '':
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : PasswordResetForm(initial={'email' : request.POST.get('email')}), 'next' : request.POST.get('next')})
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result['success']:
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : PasswordResetForm(initial={'email' : request.POST.get('email')}), 'next' : request.POST.get('next')})
        return super().post(request, *args, **kwargs)

class CustomLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        #recaptcha validation
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if recaptcha_response == '':
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : AuthenticationForm(initial={'username' : request.POST.get('username')}), 'next' : request.POST.get('next')})
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result['success']:
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : AuthenticationForm(initial={'username' : request.POST.get('username')}), 'next' : request.POST.get('next')})
        return super().post(request, *args, **kwargs)

class CustomAdminLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return redirect(reverse('admin:index'))
            else:
                messages.error(request ,"You don't have permission to access the admin section.")
                return redirect(reverse('mainapp:index'))
        return super().get(request, *args, **kwargs)
    def post(self, request, *args, **kwargs):
        #recaptcha validation
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if recaptcha_response == '':
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : AuthenticationForm(initial={'username' : request.POST.get('username')}), 'next' : request.POST.get('next')})
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = r.json()

        if not result['success']:
            messages.error(request, 'Invalid reCAPTCHA. Please try again.')
            return render(request, self.template_name, {'form' : AuthenticationForm(initial={'username' : request.POST.get('username')}), 'next' : request.POST.get('next')})
        return super().post(request, *args, **kwargs)

class RegisterView(View):
    form_class  = RegisterForm
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect(reverse('user_auth:profile'))
        form = self.form_class()
        return render(request, self.template_name, {'form' : form, 'next' : request.GET.get('next')})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            #recaptcha validation
            recaptcha_response = request.POST.get('g-recaptcha-response')
            if recaptcha_response == '':
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})
            data = {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()

            if not result['success']:
                messages.error(request, 'Invalid reCAPTCHA. Please try again.')
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})
            
            new_username = form.cleaned_data['username']
            new_password = form.cleaned_data['password']
            new_email = form.cleaned_data['email']

            if get_user_model().objects.filter(username__iexact=new_username).exists():
                messages.error(request, "Username not available, choose a different one")
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})
            if new_email != '' and get_user_model().objects.filter(email__iexact=new_email).exists():
                messages.error(request, "Email not available, choose a different one")
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})
            
            #validate password
            try:
                validate_password(new_password)
            except exceptions.ValidationError as e:
                form.errors['password'] = list(e.messages)
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})

            user = get_user_model().objects.create_user(username=new_username, password=new_password, email=new_email)
            user = authenticate(username=new_username, password=new_password)
            userprofile = UserProfile(user=user)
            userprofile.save()
            #create default room subscriptions
            for topic_name in settings.DEFAULT_TOPICS:
                if Topic.objects.filter(name=topic_name).exists():
                    topic = Topic.objects.get(name=topic_name)
                else:
                    topic = Topic(name=topic_name, title=topic_name)
                    topic.save()
                subscription = Subscription(user=user, topic=topic)
                subscription.save()
            if user is not None:
                login(request, user)
                redirect_to = request.POST.get('next', reverse('mainapp:index'))
                if is_safe_url(redirect_to):
                    return redirect(redirect_to)
                else:
                    messages.success(request, "Welcome to Hackers Chat!")
                    return redirect(reverse('mainapp:index'))
        else:
            return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})

class ProfileView(LoginRequiredMixin, View):
    form_class = ProfileForm
    template_name = 'registration/profile.html'

    def get(self, request, *args, **kwargs):
        data = {'about' : request.user.userprofile.about, 'email' : request.user.email}
        form = self.form_class(initial = data)
        return render(request, self.template_name, {'form' : form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, initial={'email' : request.user.email, 'about' : request.user.userprofile.about})
        if form.is_valid():
            if form.has_changed():
                user = request.user
                
                for field in form.changed_data:
                    if field == 'email':
                        if form.cleaned_data[field] != '' and User.objects.filter(email=form.cleaned_data[field]).exclude(id=user.id).exists():
                            messages.error(request, "Email address is already in use")
                            return redirect(reverse('user_auth:profile'))
                    setattr(user, field, form.cleaned_data[field])
                user.save()
                user.userprofile.about = form.cleaned_data['about']
                user.userprofile.save()
                messages.success(request, "Profile has been updated")
                return redirect(reverse('user_auth:profile'))
            else:
                messages.info(request, "Data has not been changed")
                return redirect(reverse('user_auth:profile'))
        else:
            messages.error(request, "Invalid form data")
            return redirect(reverse('user_auth:profile'))

class PublicUserProfileView(View):
    template_name = 'registration/public_user_profile.html'

    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        return render(request, self.template_name, {'user' : user})