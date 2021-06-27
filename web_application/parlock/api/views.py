from django.http.request import HttpRequest
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, HttpResponseNotModified
from django.http import JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from central.models import *
from django.views.decorators.csrf import csrf_exempt
import secrets
import string

# Create your views here.

# Dev note: security comes later.


@csrf_exempt
def locker_add_activity(request, locker_id: int, activity_type: str):
    try:
        lb = get_object_or_404(LockerBase, pk=locker_id)
        if LockerBase.verify(request.POST["v_code"]) != lb:
            return HttpResponseBadRequest()
        else:
            activity_type = activity_type.lower()
            if activity_type == "online":
                # report to webserver that the locker base is online.
                if lb.add_activity(activity_type=LockerActivity.ActivityType.ONLINE, locker_unit=None):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseNotModified()
            elif activity_type == "offline":
                # report to webserver that the locker base is offline.
                if lb.add_activity(activity_type=LockerActivity.ActivityType.OFFLINE, locker_unit=None):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseNotModified()
            elif activity_type == "register":
                # reports locker units connected to webserver.
                lu = get_object_or_404(LockerUnit, pk=request.POST["unit_id"])
                if lb.add_activity(activity_type=LockerActivity.ActivityType.REGISTER, locker_unit=lu):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseNotModified()
            elif activity_type == "change":
                # requests for a change in verification code.
                la = lb.change_v_code()
                if isinstance(la, LockerActivity):
                    return JsonResponse({"success": True, "v_code": lb.verification_code})
                else:
                    return HttpResponseNotModified()
            elif activity_type == "parcel":
                # queries the webserver if the parcel belongs to this lockerbase.
                parcel = get_object_or_404(Parcel, tracking_number=request.POST["tn"])
                pa = parcel.add_activity(locker_base=lb, activity_type=ParcelActivity.ActivityType.QUERY)
                if pa and isinstance(pa, ParcelActivity):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseForbidden()
            elif activity_type == "scandim":
                # informs the webserver that the parcel just had its dimensions scanned.
                parcel = get_object_or_404(Parcel, tracking_number=request.POST["tn"])
                pa = parcel.add_activity(locker_base=lb, activity_type=ParcelActivity.ActivityType.CHECKIN)
                if pa and isinstance(pa, ParcelActivity):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseForbidden()
            elif activity_type == "deposit":
                # is a set of two
                # UNLOCK - DEPOSIT_REQ if complete=false
                # LOCK - DEPOSIT if complete=true
                pass

            else:
                return HttpResponseNotFound()
    except ObjectDoesNotExist:
        return HttpResponseBadRequest()
    except KeyError:
        return HttpResponseBadRequest()


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
