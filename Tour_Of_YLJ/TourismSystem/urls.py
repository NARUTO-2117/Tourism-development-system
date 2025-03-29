from django.urls import path
from . import views

urlpatterns = [
     path("", views.login, name="login"),
     path("index", views.index, name="index"),
     path("attractions", views.attractions, name="attractions"),
     path("log", views.login, name="log"),
     path("mine", views.mine, name="mine"),
]    