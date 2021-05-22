from django.urls import path

from . import views

urlpatterns = [
    path("locker/<int:locker_base_id>/activity/query", views.locker_base_query_activity),
    path("locker/<int:locker_base_id>/<int:locker_unit_id>/activity/add/<int:activity_type>", views.locker_add_activity),
    # path("parcel/<int:parcel_id>/activity/add/<int:activity_type>", views.locker_add_activity),
]
