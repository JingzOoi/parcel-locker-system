from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from .models import LockerBase, Parcel
from .forms import ParcelForm

# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    else:
        return HttpResponse(f"you are logged in as {request.user.username}. <a href='logout/'>Logout</a>")


# home view

def home(request):
    context_dict = {}
    if request.user.is_authenticated:
        context_dict["parcel_list"] = [parcel for parcel in Parcel.objects.filter(recipient=request.user)]
    else:
        context_dict["locker_list"] = [lb for lb in LockerBase.objects.all()]
    return render(request, "home.html", context=context_dict)

# profile


def profile(request):
    return HttpResponse("Profile")

# parcel info


def parcels(request):
    return HttpResponse("parcels")


def add_parcel_action(request):
    context_dict = {}
    if request.method == "POST":
        f = ParcelForm(request.POST)
        new_parcel = f.save(commit=False)
        new_parcel.recipient = request.user
        context_dict["form"] = f
        new_parcel.save()
    else:
        context_dict["form"] = ParcelForm()
    return render(request, "parcel/register.html", context=context_dict)


def lockers(request):
    return HttpResponse("lockers")
