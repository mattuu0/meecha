from django.shortcuts import render
from django.http import JsonResponse,HttpResponse

# Create your views here.
def get_user_info(request):
    if request.user.is_authenticated:
        json_data = {
            "username" : request.user.username,
            "userid" : request.user.userid,
            "email" : request.user.email
        }

        return JsonResponse(json_data, safe=False)
    else:
        return HttpResponse(status=401)