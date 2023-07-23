from django.urls import path
from .views import main_view,post_geo_data

urlpatterns = [
    path("",main_view),
    path("post_data",post_geo_data)
]    

