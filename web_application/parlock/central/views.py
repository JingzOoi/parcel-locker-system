from django import http
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import LockerBase, Parcel, ParcelActivity
from .forms import ParcelForm
from datetime import datetime
# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    else:
        return HttpResponse(f"you are logged in as {request.user.username}. <a href='logout/'>Logout</a>")


# home view

def home(request):
    context_dict = {}
    return render(request, "home.html")

# profile


def profile(request):
    return HttpResponse("Profile")

# parcel info


def parcel(request):
    context_dict = {
        "in_progress": [],
        "completed": []
    }
    parcel_qs = Parcel.objects.filter(recipient=request.user)
    for parcel in parcel_qs:
        if parcel.last_seen_activity().type == 7:
            context_dict["completed"].append(parcel)
        else:
            context_dict["in_progress"].append(parcel)

    context_dict["parcel_dict"] = context_dict
    return render(request, "parcel/main.html", context=context_dict)


def parcel_details(request, parcel_id):
    context_dict = {}
    parcel = get_object_or_404(Parcel, id=parcel_id)
    assert parcel.recipient == request.user, "You are FORBIDDEN from performing this action. FORBIDDEN"
    parcel_activity = parcel.activities()
    context_dict["parcel_activity_latest"] = parcel_activity.pop(0)
    context_dict["parcel_activity_history"] = parcel_activity
    context_dict["parcel"] = parcel
    return render(request, "parcel/details.html", context=context_dict)


def add_parcel_action(request):
    context_dict = {}
    if request.method == "POST":
        f = ParcelForm(request.POST)
        if f.is_valid():
            new_parcel = f.save(commit=False)
            new_parcel.recipient = request.user
            new_parcel.save()
            ParcelActivity(parcel=new_parcel, _type=ParcelActivity.ActivityType.REGISTER.value, qr_data=None, associated_locker_activity=None).save()
            return http.HttpResponseRedirect("profile/")
        else:
            context_dict["form"] = f
    else:
        context_dict["form"] = ParcelForm()
    return render(request, "parcel/register.html", context=context_dict)


def lockers(request):
    return HttpResponse("lockers")
