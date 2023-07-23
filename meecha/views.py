from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
import json
from .models import Geo_Data

from accounts.models import CustomUser
from .models import Friend_request
from uuid import uuid4

# Create your views here.
def main_view(request):

    """
    TODO リリース時に削除する

    CustomUser.objects.all().delete()
    # Create your tests here.

    test_users = []
    for num in range(2000):
        user_data = CustomUser()
        user_data.set_password("password")
        user_data.email = f"test{num}_devtest@test.com"
        user_data.username = f"test{num}_devtest"
        user_data.userid = uuid4()
        
        print(num)

        user_data.save()
    """

    #Friend_request.objects.all().delete()
        
    return render(request,"meecha/index.html")

def post_geo_data(request):
    try:
        json_body = request.body.decode("utf-8")
        body = dict(json.loads(json_body))

        json_data = {
            "message":"ok"
        }
        
        if request.user.is_authenticated:
            #user_id = sha3_512(str(request.user.email).encode("utf-8")).hexdigest()   #識別ID (メールをハッシュにしたもの)

            user_id = ""
            try:
                #既にデータが存在するか
                geo_data = Geo_Data.objects.get(userid=user_id)
                #geo_data = Geo_Data.objects.select_related("userid").get(user_id)
            except Geo_Data.DoesNotExist:
                #存在しなかったら作成する
                geo_data = Geo_Data()
                geo_data.userid = user_id

            geo_data.latitude = body.get("latitude",0)
            geo_data.longitude = body.get("longitude",0)
            geo_data.save()

            print(request.user.userid)

        return JsonResponse(json_data, safe=False)
    except:
        import traceback
        traceback.print_exc()

        return HttpResponse(status=400)

