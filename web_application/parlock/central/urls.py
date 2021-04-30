from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user='/'), name="login"),
    path("logout/", auth_views.LogoutView.as_view(redirect_field_name='/'), name="logout")
]
