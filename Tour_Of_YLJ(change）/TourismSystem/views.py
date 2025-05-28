from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import spots_1,spots_2,spots_3, TravelDiary, DiaryRating
from django.views import View
from django.db.models import Q
from django.core.paginator import Paginator
import jieba

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

@login_required
def create_diary(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        location_id = request.POST.get('location')
        
        diary = TravelDiary.objects.create(
            title=title,
            content=content,
            author=request.user,
            location_id=location_id if location_id else None
        )
        return redirect('diary_detail', diary_id=diary.id)
    
    return render(request, 'tourism/create_diary.html')

@login_required
def diary_detail(request, diary_id):
    diary = get_object_or_404(TravelDiary, id=diary_id)
    diary.views += 1
    diary.save()
    
    user_rating = None
    if request.user.is_authenticated:
        user_rating = DiaryRating.objects.filter(diary=diary, user=request.user).first()
    
    return render(request, 'tourism/diary_detail.html', {
        'diary': diary,
        'user_rating': user_rating.rating if user_rating else None
    })

@login_required
def rate_diary(request, diary_id):
    if request.method == 'POST':
        rating = float(request.POST.get('rating', 0))
        if 0 <= rating <= 5:
            diary = get_object_or_404(TravelDiary, id=diary_id)
            DiaryRating.objects.update_or_create(
                diary=diary,
                user=request.user,
                defaults={'rating': rating}
            )
            diary.add_rating(rating)
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def diary_list(request):
    sort_by = request.GET.get('sort', 'created_at')
    search_query = request.GET.get('search', '')
    location_id = request.GET.get('location', '')
    
    diaries = TravelDiary.objects.all()
    
    # 搜索功能
    if search_query:
        # 使用结巴分词进行中文分词
        search_words = jieba.cut(search_query)
        q_objects = Q()
        for word in search_words:
            q_objects |= Q(title__icontains=word) | Q(content__icontains=word)
        diaries = diaries.filter(q_objects)
    
    # 按位置筛选
    if location_id:
        diaries = diaries.filter(location_id=location_id)
    
    # 排序
    if sort_by == 'views':
        diaries = diaries.order_by('-views')
    elif sort_by == 'rating':
        diaries = diaries.order_by('-rating')
    else:
        diaries = diaries.order_by('-created_at')
    
    # 分页
    paginator = Paginator(diaries, 10)
    page = request.GET.get('page', 1)
    diaries = paginator.get_page(page)
    
    return render(request, 'tourism/diary_list.html', {
        'diaries': diaries,
        'sort_by': sort_by,
        'search_query': search_query,
        'location_id': location_id
    })

@login_required
def search_diary_content(request, diary_id):
    diary = get_object_or_404(TravelDiary, id=diary_id)
    search_term = request.GET.get('q', '')
    
    if not search_term:
        return JsonResponse({'matches': []})
    
    content = diary.get_decompressed_content()
    # 使用结巴分词进行中文分词
    search_words = jieba.cut(search_term)
    
    matches = []
    for word in search_words:
        start = 0
        while True:
            index = content.find(word, start)
            if index == -1:
                break
            # 获取匹配词前后的上下文
            context_start = max(0, index - 20)
            context_end = min(len(content), index + len(word) + 20)
            matches.append({
                'position': index,
                'context': content[context_start:context_end],
                'matched_word': word
            })
            start = index + 1
    
    return JsonResponse({'matches': matches})