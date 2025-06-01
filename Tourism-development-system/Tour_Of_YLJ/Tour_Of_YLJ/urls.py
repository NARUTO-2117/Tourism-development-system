"""
URL configuration for Tour_Of_YLJ project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from TourismSystem import views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # 根路径重定向到登录页面
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    # 无前缀的登录相关页面
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    # 所有TourismSystem相关的URL
    path('TourismSystem/', include('TourismSystem.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
