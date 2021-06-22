from django.urls import path

from . import views

urlpatterns = [
    # locker queries
    path("locker/<str:activity_type>/", views.locker),

    # parcel queries
    path("parcel/<int:activity_type>/", views.parcel)
]
