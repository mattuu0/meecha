from django.urls import path
from .views import main_view,desktop_view,setting_view,demo_view

urlpatterns = [
    path("desktop_view",desktop_view),
    path("",main_view),
    path("setting",setting_view),
    path("demo",demo_view)
]    

