from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
import json
from .models import Geo_Data

from accounts.models import CustomUser
from .models import Friend_request
from uuid import uuid4

def main_view(request):
    if request.user.is_authenticated:
        return render(request,"meecha/index.html")
    else:
        return render(request,"meecha/nologin.html")

def demo_view(request):
    if request.user.is_authenticated:
        return render(request,"meecha/demo.html")
    else:
        return render(request,"meecha/nologin.html")

def setting_view(request):
    return render(request,"meecha/settings.html")

def post_geo_data(request):
    pass 

def desktop_view(request):
    return render(request,"meecha/desktop_show.html")