from django.urls import path

from . import views

urlpatterns = [
    # locker queries
    path("locker/<int:locker_id>/<str:activity_type>/", views.locker_add_activity),
    # parcel queries
]
