from django.http.response import HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from central.models import *

# Create your views here.

# Dev note: security comes later.


def locker_add_activity(request, locker_base_id: int, locker_unit_id: int, activity_type: int):
    lb = get_object_or_404(LockerBase, pk=locker_base_id)
    lu = get_object_or_404(LockerUnit, pk=locker_unit_id) if locker_unit_id else None
    la = LockerActivity(locker_base=lb, locker_unit=lu, _type=activity_type)
    la.save()
    return HttpResponse(f"added activity {la._type} for locker {la.locker_base.name}/{la.locker_unit.name}.")


def locker_base_query_activity(request, locker_base_id):
    lb = get_object_or_404(LockerBase, pk=locker_base_id)
    la_list = get_list_or_404(LockerActivity, locker_base=lb)
    la_attr = ""
    for la in la_list:
        la_attr += f"<p>{la.datetime}, {la.locker_base}, {la.locker_unit}, {la.ActivityType(la._type).label}</p>"
    return HttpResponse(la_attr)
