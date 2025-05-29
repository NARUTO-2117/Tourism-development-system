from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Attraction, Diary, DiaryComment, DiaryLike
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from .forms import DiaryForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

# 确保MEDIA_URL和MEDIA_ROOT在settings中正确配置
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create your views here.

def attractions(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    # 支持按热度、评分、类别、关键字筛选和排序
    sort = request.GET.get("sort", "popularity")  # 默认按热度
    category = request.GET.get("category", "")
    keyword = request.GET.get("keyword", "")
    attractions = Attraction.objects.all()
    if category:
        attractions = attractions.filter(category=category)
    if keyword:
        attractions = attractions.filter(keywords__icontains=keyword)
    if sort == "rating":
        attractions = attractions.order_by("-rating", "-rating_count")
    else:
        attractions = attractions.order_by("-popularity")
    paginator = Paginator(attractions, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    categories = Attraction.CATEGORY_CHOICES
    return render(request, "TourismSystem/attractions.html", {
        "page_obj": page_obj,
        "categories": categories,
        "current_category": category,
        "current_keyword": keyword,
        "sort": sort,
    })

@login_required
def log(request):
    # 支持按热度、评分、时间排序和筛选
    sort = request.GET.get("sort", "popularity")
    keyword = request.GET.get("keyword", "")
    diaries = Diary.objects.select_related('author', 'attraction')
    if keyword:
        diaries = diaries.filter(
            Q(title__icontains=keyword) |
            Q(content__icontains=keyword) |
            Q(attraction__name__icontains=keyword)
        )
    if sort == "rating":
        diaries = diaries.order_by("-rating", "-created_at")
    elif sort == "time":
        diaries = diaries.order_by("-created_at")
    else:
        diaries = diaries.order_by("-popularity", "-created_at")
    # 分页
    paginator = Paginator(diaries, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "TourismSystem/log.html", {
        "page_obj": page_obj,
        "sort": sort,
        "keyword": keyword,
    })

def login(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/login.html")

@login_required
def mine(request):
    user = request.user
    diaries = Diary.objects.filter(author=user).select_related('attraction').order_by('-created_at')
    # 分页，每页10条
    from django.core.paginator import Paginator
    paginator = Paginator(diaries, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "TourismSystem/mine.html", {
        "page_obj": page_obj,
    })

class index(View):

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse("login"))
        # 热门推荐：按热度排序取前8个
        hot_attractions = Attraction.objects.order_by("-popularity")[:8]
        # 热门城市排行：按热度排序取前10个
        city_rank_list = Attraction.objects.order_by("-popularity")[:10]
        context = {
            "hot_attractions": hot_attractions,
            "spots_1_list": city_rank_list,  # 让模板继续用spots_1_list变量
        }
        return render(request, "TourismSystem/index.html", context)
    
    def post(self, request):
    	# POST请求接收输入框内容q
        qParams = request.POST.get('q')
        if not qParams:
            return JsonResponse({
                'code': 400,
                'msg': '缺少参数'
            })
        # 用 Attraction 模型进行多字段模糊查询
        article = Attraction.objects.filter(
            Q(name__icontains=qParams) | Q(category__icontains=qParams) | Q(epithet__icontains=qParams)
        ).values_list("id", "name")
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
    # 用Attraction模型替换spots_1
    attraction = get_object_or_404(Attraction, id=spot_id)
    # 获取该景点下所有日记，按热度和时间排序
    diaries = attraction.diaries.order_by('-popularity', '-created_at')
    # 判断当前用户是否已上传过日记
    user_diary = None
    if request.user.is_authenticated:
        user_diary = Diary.objects.filter(author=request.user, attraction=attraction).first()
    context = {
        "attraction": attraction,
        "diaries": diaries,
        "user_diary": user_diary,
    }
    return render(request, "TourismSystem/attraction_detail.html", context)

@login_required
def upload_diary(request, attraction_id):
    attraction = get_object_or_404(Attraction, id=attraction_id)
    user = request.user

    # 检查是否已上传过日记
    existing_diary = Diary.objects.filter(author=user, attraction=attraction).first()
    if existing_diary and not existing_diary.can_modify_rating:
        # 已上传且评分不可再改，禁止再次上传
        return render(request, "TourismSystem/diary_upload.html", {
            "error": "您已上传过该景点的日记且评分已修改过，不能再次上传。",
            "attraction": attraction,
            "diary": existing_diary,
            "form": DiaryForm(instance=existing_diary)
        })

    if request.method == "POST":
        form = DiaryForm(request.POST, request.FILES, instance=existing_diary)
        if form.is_valid():
            diary = form.save(commit=False)
            diary.author = user
            diary.attraction = attraction
            # 评分只能修改一次
            if existing_diary:
                if existing_diary.can_modify_rating:
                    diary.can_modify_rating = False
                else:
                    # 已经修改过评分，不能再改
                    return render(request, "TourismSystem/diary_upload.html", {
                        "error": "您已修改过评分，不能再次修改。",
                        "attraction": attraction,
                        "diary": existing_diary,
                        "form": form
                    })
            diary.save()
            # 更新景点评分
            diaries = Diary.objects.filter(attraction=attraction)
            total_score = sum([d.rating for d in diaries])
            attraction.rating = round(total_score / diaries.count(), 1)
            attraction.rating_count = diaries.count()
            attraction.save()
            return redirect('diary_detail', diary_id=diary.id)
    else:
        form = DiaryForm(instance=existing_diary)

    return render(request, "TourismSystem/diary_upload.html", {
        "form": form,
        "attraction": attraction,
        "diary": existing_diary
    })

def diary_detail(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id)
    return render(request, "TourismSystem/diary_detail.html", {
        "diary": diary
    })

@login_required
@require_POST
def diary_like(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id)
    user = request.user
    # 每人只能点赞一次
    if not DiaryLike.objects.filter(diary=diary, user=user).exists():
        DiaryLike.objects.create(diary=diary, user=user)
        diary.popularity += 1
        diary.save()
    return redirect('diary_detail', diary_id=diary.id)

@login_required
@require_POST
def diary_comment(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id)
    content = request.POST.get("content")
    if content:
        DiaryComment.objects.create(diary=diary, author=request.user, content=content)
    return redirect('diary_detail', diary_id=diary.id)

@login_required
def delete_diary(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id, author=request.user)
    attraction_id = diary.attraction.id
    if request.method == "POST":
        diary.delete()
        messages.success(request, "日记已删除。")
        return redirect('mine')
    return render(request, "TourismSystem/diary_confirm_delete.html", {"diary": diary})

def handle_uploaded_file(f):
    fs = FileSystemStorage()
    filename = fs.save(f.name, f)
    return fs.url(filename)

def upload_image(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        # 处理上传的文件（保存到文件系统、数据库等）
        image_url = handle_uploaded_file(image)
        return JsonResponse({'image_url': image_url})
    return JsonResponse({'error': '无效请求'}, status=400)
