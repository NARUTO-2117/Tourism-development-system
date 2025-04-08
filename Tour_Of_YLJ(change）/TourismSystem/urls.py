from django.urls import path
from . import views

urlpatterns = [
     path("attractions", views.attractions, name="attractions"),
     path("log", views.log, name="log"),
     path("mine", views.mine, name="mine"),
     path("", views.index, name="index"),
]