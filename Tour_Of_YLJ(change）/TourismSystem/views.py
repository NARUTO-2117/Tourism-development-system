from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from .models import spots_1,spots_2,spots_3
from django.http import JsonResponse
from django.views import View
from django.db.models import Q

 # Create your views here.

def attractions(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/attractions.html")

def log(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/log.html")

def login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/login.html")

def mine(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/mine.html")

class index(View):

    def get(self,request):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        spot_list = spots_1.objects.order_by("-popularity")[:10]
        context = {"spots_1_list": spot_list}
        return render(request, "TourismSystem/index.html", context)
    
    def post(self, request):
    	# POST请求接收输入框内容q
        qParams = request.POST.get('q')
        if not qParams:
            return JsonResponse({
                'code': 400,
                'msg': '缺少参数'
            })
        # 使用 Q语句 进行 多字段模糊查询
        article = spots_1.objects.filter(
            Q(name__icontains=qParams) | Q(category__icontains=qParams) | Q(epithet__icontains=qParams)).values_list("id", "name")
        res_list = []
        try:
            for item in article:
                search_obj = {'id': item[0], 'name': item[1]}
                res_list.append(search_obj)
        except Exception as e:
            print("搜索报错：", e)
        return JsonResponse({
            'code': 200,
            'data': res_list,
        })

def attraction_detail(request, spot_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    try:
        spot = spots_1.objects.get(id=spot_id)
        context = {
            "spot": spot,
            "spot_name": spot.name,
            "spot_category": spot.category,
            "spot_epithet": spot.epithet,
            "spot_popularity": spot.popularity,
            "spot_rating": spot.rating
        }
        return render(request, "TourismSystem/attraction_detail.html", context)
    except spots_1.DoesNotExist:
        return HttpResponseRedirect(reverse("attractions"))