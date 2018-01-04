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
from django.http import HttpResponse

class RegisterView(View):
    form_class  = RegisterForm
    template_name = 'registration/register.html'

    def get(self, request, *args, **kwargs):
        return HttpResponse("Registration is currently disabled because of 4chan trolls. If you want an invite send an email to ploggingdev @ gmail")
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect(reverse('user_auth:profile'))
        form = self.form_class()
        return render(request, self.template_name, {'form' : form, 'next' : request.GET.get('next')})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_username = form.cleaned_data['username']
            new_password = form.cleaned_data['password']
            new_email = form.cleaned_data['email']

            if get_user_model().objects.filter(username=new_username).exists():
                messages.error(request, "Username not available, choose a different one")
                return render(request, self.template_name, {'form' : form, 'next' : request.POST.get('next')})
            if new_email != '' and get_user_model().objects.filter(email=new_email).exists():
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
            if user is not None:
                login(request, user)
                redirect_to = request.POST.get('next', reverse('mainapp:index'))
                if is_safe_url(redirect_to):
                    return redirect(redirect_to)
                else:
                    messages.success(request, "Welcome to Bored Hackers!")
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