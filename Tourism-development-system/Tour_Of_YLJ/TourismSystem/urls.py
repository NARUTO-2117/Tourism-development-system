from django.urls import path
from . import views
from TourismSystem.views import index

urlpatterns = [
     path("attractions", views.attractions, name="attractions"),
     path("attractions/<int:spot_id>", views.attraction_detail, name="attraction_detail"),
     path("log", views.log, name="log"),
     path("mine", views.mine, name="mine"),
     path("", index.as_view(), name="index"),
     path('diary/<int:diary_id>/', views.diary_detail, name='diary_detail'),
     path('diary/<int:diary_id>/like/', views.diary_like, name='diary_like'),
     path('diary/<int:diary_id>/comment/', views.diary_comment, name='diary_comment'),
     path('attraction/<int:spot_id>/', views.attraction_detail, name='attraction_detail'),
     path('attraction/<int:attraction_id>/upload_diary/', views.upload_diary, name='upload_diary'),
     path('diary/<int:diary_id>/delete/', views.delete_diary, name='delete_diary'),
]