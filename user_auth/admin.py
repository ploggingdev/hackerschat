from django.contrib import admin
from .models import UserProfile
from .forms import AdminUserProfileForm

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = AdminUserProfileForm
    list_display = ('user' ,'created')