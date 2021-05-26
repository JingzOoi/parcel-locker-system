from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as forms

from . import views

urlpatterns = [
    path("", views.home),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("lockers/", views.lockers, name="locker"),
    path("parcel/", views.parcels, name="parcel"),
    path("parcel/register/", views.add_parcel_action, name="parcel-register"),
]
