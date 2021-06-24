from django import http
from django.http.response import HttpResponse, HttpResponseForbidden, HttpResponseGone
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from .models import LockerActivity, LockerBase, Parcel, ParcelActivity
from .forms import ParcelForm
from datetime import datetime
from django.contrib.postgres.search import SearchVector
from django.contrib.auth.decorators import login_required
# Create your views here.


# home view

def home(request):
    context_dict = {}
    if request.user.is_authenticated and request.user.is_admin:
        context_dict["latest_pa"] = ParcelActivity.objects.order_by("-datetime")[:10]
        context_dict["latest_la"] = LockerActivity.objects.order_by("-datetime")[:10]
    return render(request, "home.html", context=context_dict)

# profile


def profile(request):
    return HttpResponse("Profile")

# parcel info


def parcel(request):
    context_dict = {
        "in_progress": [],
        "completed": []
    }
    for parcel in request.user.parcels():
        if parcel.is_complete():
            context_dict["completed"].append(parcel)
        else:
            context_dict["in_progress"].append(parcel)

    context_dict["parcel_dict"] = context_dict
    return render(request, "parcel/main.html", context=context_dict)


def parcel_details(request, parcel_id):
    context_dict = {}
    parcel = get_object_or_404(Parcel, id=parcel_id)
    if parcel.recipient != request.user:
        raise PermissionDenied
    parcel_activity = parcel.activities()
    context_dict["parcel_activity_latest"] = parcel_activity.pop(0)
    context_dict["parcel_activity_history"] = parcel_activity
    context_dict["parcel"] = parcel
    return render(request, "parcel/details.html", context=context_dict)


@login_required(login_url="login")
def add_parcel_action(request):
    context_dict = {}
    if request.method == "POST":
        f = ParcelForm(request.POST)
        if f.is_valid():
            new_parcel = f.save(commit=False)
            new_parcel.recipient = request.user
            new_parcel.save()
            ParcelActivity(parcel=new_parcel, type=ParcelActivity.ActivityType.REGISTER.value, associated_locker_activity=None).save()
            return http.HttpResponseRedirect("parcel/")
        else:
            context_dict["form"] = f
    elif request.method == "GET" and "locker" in request.GET:
        try:
            lb = LockerBase.objects.get(pk=request.GET["locker"])
            context_dict["form"] = ParcelForm({"destination_locker": lb})
        except LockerBase.DoesNotExist:
            context_dict["form"] = ParcelForm()
    else:
        context_dict["form"] = ParcelForm()
    return render(request, "parcel/register.html", context=context_dict)


@login_required(login_url="login")
def parcel_withdraw_application(request, parcel_id):
    # submit an application to withdraw parcel.
    context_dict = {}
    parcel = get_object_or_404(Parcel, pk=parcel_id)
    if not parcel.recipient == request.user:
        return HttpResponseForbidden()
    else:
        pa = parcel.add_activity(locker_base=None, activity_type=ParcelActivity.ActivityType.WITHDRAWAPP)
        if isinstance(pa, ParcelActivity):
            context_dict["qr_data"] = parcel.make_retrieval_code()
            return render(request, "parcel/withdraw.html", context=context_dict)
        else:
            return HttpResponseGone()


def lockers(request):
    context_dict = {}
    if request.user.is_authenticated:
        most_used = [parcel.destination_locker for parcel in request.user.parcels()]
        context_dict["most_used"] = max(set(most_used), key=most_used.count)
    if request.method == "POST":
        kw = request.POST.get("keyword", None)
        if kw:
            context_dict["results"] = [lb for lb in LockerBase.objects.annotate(search=SearchVector("name", "street_address", "city", "state", "zip_code")).filter(search=kw)]
    return render(request, "locker/main.html", context=context_dict)
