from django.urls import path
from . import views
from TourismSystem.views import index

urlpatterns = [
     path("attractions", views.attractions, name="attractions"),
     path("attractions/<int:spot_id>", views.attraction_detail, name="attraction_detail"),
     path("log", views.log, name="log"),
     path("mine", views.mine, name="mine"),
     path("", index.as_view(), name="index"),
     path('diary/create/', views.create_diary, name='create_diary'),
     path('diary/<int:diary_id>/', views.diary_detail, name='diary_detail'),
     path('diary/<int:diary_id>/rate/', views.rate_diary, name='rate_diary'),
     path('diary/list/', views.diary_list, name='diary_list'),
     path('diary/<int:diary_id>/search/', views.search_diary_content, name='search_diary_content'),
]