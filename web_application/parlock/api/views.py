from django.http.request import HttpRequest
from django.http.response import Http404, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from central.models import *

# Create your views here.

# Dev note: security comes later.


def locker(request, activity_type: str):
    if request.method == "GET" and "v" in request.GET:
        try:
            lb = LockerBase.verify(v_code=request.GET["v"])
            if lb:
                if activity_type.lower() in ("online"):
                    la = lb.add_activity(activity_type=LockerActivity.ActivityType.ONLINE, locker_unit=None)
                elif activity_type.lower() in ("offline"):
                    la = lb.add_activity(activity_type=LockerActivity.ActivityType.OFFLINE, locker_unit=None)
                else:
                    raise Http404
                if la:
                    return HttpResponse(repr(la))
            else:
                raise Http404
        except ObjectDoesNotExist:
            raise Http404


def parcel(request, activity_type: int):
    if request.method == "GET" and "v" in request.GET:
        try:
            lb = LockerBase.verify(v_code=request.GET["v"])
            if "tn" in request.GET:
                parcel = get_object_or_404(Parcel, tracking_number=request.GET["tn"])
                if parcel.add_activity(lb, activity_type):
                    return HttpResponse(f"{parcel.id}")
                else:
                    raise Http404
            else:
                raise Http404
        except ObjectDoesNotExist:
            raise Http404

    elif request.method == "POST" and "v" in request.POST:
        lb = get_object_or_404(LockerBase, verification_code=request.POST["v"])

    else:
        raise Http404
