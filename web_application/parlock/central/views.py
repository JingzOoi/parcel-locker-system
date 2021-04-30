from django.http.response import HttpResponse
from django.shortcuts import redirect, render

# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")
    else:
        return HttpResponse(f"you are logged in as {request.user.username}. <a href='logout/'>Logout</a>")
