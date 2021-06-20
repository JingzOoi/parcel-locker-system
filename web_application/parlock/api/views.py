from django.http.request import HttpRequest
from django.http.response import Http404, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from central.models import *

# Create your views here.

# Dev note: security comes later.


def locker_add_activity(request, locker_base_id: int, locker_unit_id: int, activity_type: int):
    lb = get_object_or_404(LockerBase, pk=locker_base_id)
    lu = get_object_or_404(LockerUnit, pk=locker_unit_id) if locker_unit_id != 0 else None
    la = LockerActivity(locker_base=lb, locker_unit=lu, type=activity_type)
    la.save()
    return HttpResponse(f"added activity {la.type} for locker {la.locker_base.name}")


def locker_base_query_activity(request, locker_base_id):
    lb = get_object_or_404(LockerBase, pk=locker_base_id)
    la_list = get_list_or_404(LockerActivity, locker_base=lb)
    la_attr = ""
    for la in la_list:
        la_attr += f"<p>{la.datetime}, {la.locker_base}, {la.locker_unit}, {la.ActivityType(la._type).label}</p>"
    return HttpResponse(la_attr)


def parcel_query(request, locker_base_id: int):
    lb = get_object_or_404(LockerBase, pk=locker_base_id)
    if request.method == "GET":
        tn = request.GET["tn"]
        parcel = get_object_or_404(Parcel, tracking_number=tn)
        if parcel.destination_locker != lb:
            raise Http404
        else:
            la = LockerActivity(locker_base=lb, locker_unit=None, type=5)
            la.save()
            pl = ParcelActivity(parcel=parcel, type=2, associated_locker_activity=la)
            pl.save()
            return JsonResponse({"parcel_activity": hash(pl)})
