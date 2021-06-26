from django.http.request import HttpRequest
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, HttpResponseNotModified
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from central.models import *
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

# Create your views here.


@require_POST
@csrf_exempt
def locker_add_activity(request, locker_id: int, activity_type: str):
    """
    Concentrated endpoint for the locker base to query the webserver.
    """
    try:
        lb = get_object_or_404(LockerBase, pk=locker_id)
        if LockerBase.verify(request.POST["verification_code"]) != lb:
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

                    return JsonResponse({
                        "success": True,
                        "length": lu.length,
                        "width": lu.width,
                        "height": lu.height
                    })
                else:
                    return HttpResponseNotModified()
            elif activity_type == "change":
                # requests for a change in verification code.
                la = lb.change_v_code()
                if isinstance(la, LockerActivity):
                    return JsonResponse({"success": True, "verification_code": lb.verification_code})
                else:
                    return HttpResponseNotModified()
            elif activity_type == "parcel":
                # queries the webserver if the parcel belongs to this lockerbase.
                parcel = get_object_or_404(Parcel, tracking_number=request.POST["tracking_number"])
                pa = parcel.add_activity(locker_base=lb, activity_type=ParcelActivity.ActivityType.QUERY)
                if pa and isinstance(pa, ParcelActivity):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseForbidden()
            elif activity_type == "scandim":
                # informs the webserver that the parcel just had its dimensions scanned.
                parcel = get_object_or_404(Parcel, tracking_number=request.POST["tracking_number"])
                pa = parcel.add_activity(locker_base=lb, activity_type=ParcelActivity.ActivityType.CHECKIN)
                if pa and isinstance(pa, ParcelActivity):
                    return JsonResponse({"success": True})
                else:
                    return HttpResponseForbidden()
            elif activity_type == "deposit":
                # is a set of two
                # UNLOCK - DEPOSIT_REQ if complete=false
                # LOCK - DEPOSIT if complete=true
                parcel = get_object_or_404(Parcel, tracking_number=request.POST["tracking_number"])
                lu = get_object_or_404(LockerUnit, pk=request.POST["unit_id"])
                if "complete" in request.POST:
                    is_complete = eval(request.POST["complete"])
                    if isinstance(is_complete, bool) and is_complete:
                        pa = parcel.add_activity(
                            locker_base=lb,
                            locker_unit=lu,
                            activity_type=ParcelActivity.ActivityType.DEPOSIT
                        )
                    else:
                        pa = parcel.add_activity(
                            locker_base=lb,
                            locker_unit=lu,
                            activity_type=ParcelActivity.ActivityType.DEPOSITREQ
                        )
                    if pa and isinstance(pa, ParcelActivity):
                        return JsonResponse({"success": True})
                    else:
                        return JsonResponse({"success": False})
                else:
                    return HttpResponseForbidden()

            elif activity_type == "withdraw":
                # see above, set of two
                parcel = Parcel.verify_retrieval_code(qr_data=request.POST["qr_data"])
                lu = get_object_or_404(LockerUnit, pk=request.POST["unit_id"])
                if "complete" in request.POST:
                    is_complete = eval(request.POST["complete"])
                    if isinstance(is_complete, bool) and is_complete:
                        pa = parcel.add_activity(
                            locker_base=lb,
                            locker_unit=lu,
                            activity_type=ParcelActivity.ActivityType.WITHDRAW
                        )
                    else:
                        pa = parcel.add_activity(
                            locker_base=lb,
                            locker_unit=lu,
                            activity_type=ParcelActivity.ActivityType.WITHDRAWREQ
                        )
                    if pa and isinstance(pa, ParcelActivity):
                        return JsonResponse({"success": True})
                    else:
                        return JsonResponse({"success": False})
                else:
                    return HttpResponseForbidden()

            elif activity_type == "withdraw-qr":
                # when the recipient scans qr code
                p = Parcel.verify_retrieval_code(qr_data=request.POST["qr_data"])
                if p is None:
                    return HttpResponseNotFound()
                elif p is False:
                    return JsonResponse({"success": False})
                elif isinstance(p, Parcel):
                    pa = p.add_activity(
                        locker_base=lb,
                        activity_type=ParcelActivity.ActivityType.WITHDRAWQR
                    )
                    if pa and isinstance(pa, ParcelActivity):
                        return JsonResponse({"success": True})
                    else:
                        return JsonResponse({"success": False})

            else:
                return HttpResponseNotFound()
    except ObjectDoesNotExist as e:
        logging.error(e)
        return HttpResponseBadRequest()
    except KeyError:
        return HttpResponseBadRequest()
