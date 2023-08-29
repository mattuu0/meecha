from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.shortcuts import redirect

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
    
def redirect_login(request):
    response = redirect('/accounts/login') # /app/redirect_viewに遷移させる
    return response

def upload_icon(request):
    if request.user.is_authenticated:
        pass
