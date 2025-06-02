from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('attractions/', views.attractions, name='attractions'),
    path('attractions/<int:spot_id>/', views.attraction_detail, name='attraction_detail'),
    path('attractions/<int:spot_id>/upload/', views.upload_diary, name='upload_diary'),
    path('diary/<int:diary_id>/', views.diary_detail, name='diary_detail'),
    path('diary/<int:diary_id>/like/', views.diary_like, name='diary_like'),
    path('diary/<int:diary_id>/comment/', views.diary_comment, name='diary_comment'),
    path('diary/<int:diary_id>/delete/', views.delete_diary, name='delete_diary'),
    path('log/', views.log, name='log'),
    path('mine/', views.mine, name='mine'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('api/diaries/search/', views.search_diaries, name='search_diaries'),
    path('api/attractions/search/', views.search_attractions, name='search_attractions'),
    path('search_places/', views.search_places, name='search_places'),
    
    # 美食推荐相关URL
    path('foods/', views.food_recommendation, name='food_recommendation'),
    path('foods/<int:food_id>/', views.food_detail, name='food_detail'),
    path('foods/<int:food_id>/review/', views.add_food_review, name='add_food_review'),
    path('api/foods/search/', views.search_foods, name='search_foods'),
    path('load_demo_foods/', views.load_demo_foods, name='load_demo_foods'),
]