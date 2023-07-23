from django.contrib.auth.models import AbstractUser
from django.db import models
from uuid import uuid4 

class CustomUser(AbstractUser):
    class Meta:
        verbose_name_plural = 'CustomUser'
    
    userid = models.UUIDField(primary_key=True, default=uuid4())                                #ユーザーID
    online_status = models.CharField(max_length=50,default="offline")                           #オンラインか
    last_online = models.DateTimeField(auto_now=True)                                           #最終オンライン時間
    now_connected = models.BooleanField(default=False)                                          #接続中か

    def __str__(self) -> str:
        return self.username
    
    