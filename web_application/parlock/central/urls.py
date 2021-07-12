from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as forms
from .forms import UserRegistrationForm

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.add_user_action, name="register"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("lockers/", views.lockers, name="locker-view"),
    path("parcel/", views.parcel, name="parcel"),
    path("parcel/<int:parcel_id>", views.parcel_details, name="parcel-detail"),
    path("parcel/<int:parcel_id>/withdraw", views.parcel_withdraw_application, name="parcel-withdraw"),
    path("parcel/register/", views.add_parcel_action, name="parcel-register"),
]
