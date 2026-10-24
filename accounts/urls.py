from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("skills/<int:pk>/remove/", views.remove_skill, name="remove_skill"),
    path("certifications/<int:pk>/remove/", views.remove_certification, name="remove_certification"),
    path("notifications/", views.notifications, name="notifications"),
    path("users/<int:user_id>/block/", views.block_user, name="block_user"),
    path("users/<int:user_id>/unblock/", views.unblock_user, name="unblock_user"),
]
