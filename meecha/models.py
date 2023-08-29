from django.db import models
from accounts.models import CustomUser
from uuid import uuid4
import random

verify_digest = 5
# Create your models here.
class Geo_Data(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,null=True,blank=True)           #ユーザーオブジェクト
    latitude = models.FloatField()                                           #緯度
    longitude = models.FloatField()                                          #経度            
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "位置情報データ"

class Friend_data(models.Model):
    dataid = models.UUIDField(default=uuid4,primary_key=True,editable=False)
    
    from_user =  models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name="from_user")           #送った人
    from_user_memo = models.TextField(default="")                                                                               #送った人メモ

    to_user =  models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name="to_user")               #送られた人
    to_user_memo = models.TextField(default="")                                                                                 #送られた人メモ

    timestamp = models.DateTimeField(auto_now_add=True)                                                                         #タイムスタンプ

    from_already_notify = models.BooleanField(default=False)                                                                    #既に通知したか
    to_already_notify = models.BooleanField(default=False)                                                                      #既に通知したか
    is_neared = models.BooleanField(default=False) 

    def __str__(self) -> str:
        return str(self.dataid)

def random_code():
    return str(random.randint(0,10**verify_digest)).zfill(verify_digest)

class Friend_request(models.Model):
    dataid = models.UUIDField(default=uuid4,primary_key=True,editable=False)
    
    from_user =  models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name="request_from_user")           #送った人
    to_user =  models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True,related_name="request_to_user")               #送られた人
    timestamp = models.DateTimeField(auto_now_add=True)                                                                                 #タイムスタンプ
    verify_code = models.CharField(default=random_code,max_length=4)                                                                    #承認に必要なコード

    def __str__(self) -> str:
        return str(self.dataid)

class user_setting(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)

    notify_disatance = models.IntegerField(default=50)              #通知距離