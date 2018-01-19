from django.urls import path, re_path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'user_auth'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    re_path('profile/(?P<username>[a-zA-Z0-9_-]+)/', views.PublicUserProfileView.as_view(), name='public_user_profile'),
    path(
        'login/',
        views.CustomLoginView.as_view(redirect_authenticated_user=True), name="login",
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(), name="logout"
    ),
    path(
        'password_change/',
        auth_views.PasswordChangeView.as_view(success_url=reverse_lazy('user_auth:password_change_done')), name="password_change"
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view() ,name="password_change_done"
    ),
    path(
        'password_reset/',
        views.CustomPasswordResetView.as_view(success_url=reverse_lazy('user_auth:password_reset_done'), from_email='hackerschat@ploggingdev.com'), name="password_reset"
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('user_auth:password_reset_complete')), name="password_reset_confirm"
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"
    ),
]