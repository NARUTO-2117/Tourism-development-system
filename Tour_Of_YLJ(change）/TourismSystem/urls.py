from django.urls import path
from . import views
from TourismSystem.views import index

urlpatterns = [
     path("attractions", views.attractions, name="attractions"),
     path("attractions/<int:spot_id>", views.attraction_detail, name="attraction_detail"),
     path("log", views.log, name="log"),
     path("mine", views.mine, name="mine"),
     path("", index.as_view(), name="index"),
]