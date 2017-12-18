from django.contrib import admin
from .models import UserProfile
from .forms import AdminUserProfileForm
from reversion.admin import VersionAdmin

@admin.register(UserProfile)
class UserProfileAdmin(VersionAdmin):
    form = AdminUserProfileForm
    list_display = ('user' ,'created')