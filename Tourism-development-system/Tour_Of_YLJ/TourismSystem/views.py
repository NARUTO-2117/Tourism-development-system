from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Attraction, Diary, DiaryComment, DiaryLike
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied
from .forms import DiaryForm
from django.db.models import Q, F, Count, Avg
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import json
from django.core.cache import cache
import zlib
import logging
import base64
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

# 配置日志
logger = logging.getLogger(__name__)

# 确保MEDIA_URL和MEDIA_ROOT在settings中正确配置
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Create your views here.

def load_places_data():
    # 获取数据文件的路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
    facilities_path = os.path.join(base_dir, 'data', 'facilities.json')
    
    # 读取数据
    with open(buildings_path, 'r', encoding='utf-8') as f:
        buildings = json.load(f)
    with open(facilities_path, 'r', encoding='utf-8') as f:
        facilities = json.load(f)
    
    # 过滤掉类型为"路口"的设施
    filtered_facilities = [f for f in facilities if f['type'] != '路口']
    
    # 合并数据
    return buildings + filtered_facilities

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
        "sort": sort
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

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "TourismSystem/login.html", {
                "message": "用户名或密码错误"
            })
    else:  # 处理GET请求，展示登录页面
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

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    # 获取排序方式，默认为热度排序
    sort_by = request.GET.get('sort_by', 'popularity')
    
    # 根据排序方式获取景点列表
    if sort_by == 'rating':
        city_rank_list = Attraction.objects.order_by("-rating", "-rating_count")[:10]
    elif sort_by == 'random':
        # 使用随机排序
        city_rank_list = Attraction.objects.order_by('?')[:10]
    else:  # 默认按热度排序
        city_rank_list = Attraction.objects.order_by("-popularity")[:10]
    
    # 热门推荐：按热度排序取前8个
    hot_attractions = Attraction.objects.order_by("-popularity")[:8]
    
    context = {
        "hot_attractions": hot_attractions,
        "spots_1_list": city_rank_list,
        "current_sort": sort_by,  # 传递当前排序方式到模板
    }
    return render(request, "TourismSystem/index.html", context)

def search(request):
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
            search_obj = {
                'id': item[0],
                'name': item[1],
                'url': '/TourismSystem' + reverse('attraction_detail', args=[item[0]])
            }
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
    diaries = Diary.objects.filter(attraction=attraction).order_by('-popularity', '-created_at')
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

def compress_content(content):
    """压缩日记内容"""
    try:
        # 将内容转换为字节
        content_bytes = content.encode('utf-8')
        # 使用zlib进行压缩
        compressed = zlib.compress(content_bytes)
        # 将压缩后的字节转换为base64字符串
        return base64.b64encode(compressed).decode('utf-8')
    except Exception as e:
        logger.error(f"压缩内容时发生错误: {str(e)}")
        return content

def decompress_content(compressed_content):
    """解压日记内容"""
    try:
        # 将base64字符串转换回字节
        compressed_bytes = base64.b64decode(compressed_content)
        # 使用zlib解压
        decompressed = zlib.decompress(compressed_bytes)
        # 将解压后的字节转换回字符串
        return decompressed.decode('utf-8')
    except Exception as e:
        logger.error(f"解压内容时发生错误: {str(e)}")
        return compressed_content

@login_required
def upload_diary(request, spot_id):
    attraction = get_object_or_404(Attraction, id=spot_id)
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
            
            # 压缩日记内容
            if diary.content:
                diary.content = compress_content(diary.content)
            
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
    
    # 解压日记内容
    if diary.content:
        try:
            diary.content = decompress_content(diary.content)
        except:
            # 如果解压失败，保持原内容不变
            pass
    
    return render(request, "TourismSystem/diary_detail.html", {
        "diary": diary
    })

@login_required
@require_POST
def diary_like(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id)
    user = request.user
    
    # 检查是否已经点赞
    if user in diary.likes.all():
        # 如果已经点赞，则取消点赞
        diary.likes.remove(user)
        diary.popularity = max(0, diary.popularity - 1)
        liked = False
    else:
        # 如果是新点赞，增加热度
        diary.likes.add(user)
        diary.popularity += 1
        liked = True
    
    diary.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 如果是 AJAX 请求，返回 JSON 响应
        return JsonResponse({
            'liked': liked,
            'popularity': diary.popularity,
            'likes_count': diary.likes.count()
        })
    
    # 如果是普通表单提交，重定向回日记详情页
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

@require_http_methods(["GET"])
def search_diaries(request):
    """搜索旅游日记的视图函数"""
    try:
        keyword = request.GET.get('keyword', '')
        destination = request.GET.get('destination', '')
        sort = request.GET.get('sort', 'popularity')
        page = request.GET.get('page', 1)
        
        # 构建缓存键
        cache_key = f"diary_search:{keyword}:{destination}:{sort}:{page}"
        
        # 尝试从缓存获取结果
        try:
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"从缓存获取搜索结果: {cache_key}")
                return JsonResponse(cached_result)
        except Exception as e:
            logger.error(f"缓存读取错误: {str(e)}")
        
        # 构建查询
        query = Q()
        if keyword:
            query |= Q(title__icontains=keyword)
            # 对于压缩的内容，先解压再搜索
            diaries = Diary.objects.filter(query).select_related('attraction', 'author')
            for diary in diaries:
                try:
                    if diary.content:
                        decompressed_content = decompress_content(diary.content)
                        if keyword.lower() in decompressed_content.lower():
                            query |= Q(id=diary.id)
                except:
                    continue
        if destination:
            query &= Q(attraction__name__icontains=destination)
        
        # 获取日记列表
        diaries = Diary.objects.filter(query).select_related('attraction', 'author')
        
        # 应用排序
        if sort == 'popularity':
            diaries = diaries.annotate(
                popularity_score=F('likes') * 0.4 + F('comments') * 0.3 + F('views') * 0.3
            ).order_by('-popularity_score')
        elif sort == 'rating':
            diaries = diaries.order_by('-rating')
        else:  # time
            diaries = diaries.order_by('-created_at')
        
        # 分页
        paginator = Paginator(diaries, 12)  # 每页12条
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        # 处理结果
        result = {
            'diaries': [
                {
                    'id': diary.id,
                    'title': diary.title,
                    'content': decompress_content(diary.content) if diary.content else '',
                    'attraction': {
                        'name': diary.attraction.name,
                    },
                    'author': {
                        'username': diary.author.username,
                    },
                    'popularity': diary.popularity,
                    'rating': diary.rating,
                    'created_at': diary.created_at.isoformat(),
                    'image': diary.image.url if diary.image else None,
                }
                for diary in page_obj
            ],
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
            }
        }
        
        # 尝试缓存结果
        try:
            cache.set(cache_key, result, timeout=300)  # 缓存5分钟
            logger.info(f"搜索结果已缓存: {cache_key}")
        except Exception as e:
            logger.error(f"缓存写入错误: {str(e)}")
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"搜索日记时发生错误: {str(e)}")
        return JsonResponse({
            'error': '搜索失败，请稍后重试',
            'details': str(e)
        }, status=500)

@require_http_methods(["POST"])
def like_diary(request, diary_id):
    """点赞日记的视图函数"""
    try:
        diary = Diary.objects.get(id=diary_id)
        user = request.user
        
        if user in diary.likes.all():
            diary.likes.remove(user)
            liked = False
        else:
            diary.likes.add(user)
            liked = True
        
        # 更新热度
        diary.popularity = diary.likes.count() * 0.4 + diary.comments.count() * 0.3 + diary.views * 0.3
        diary.save()
        
        return JsonResponse({
            'liked': liked,
            'popularity': diary.popularity
        })
    except Diary.DoesNotExist:
        logger.error(f"日记不存在: {diary_id}")
        return JsonResponse({'error': '日记不存在'}, status=404)
    except Exception as e:
        logger.error(f"点赞操作失败: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def search_attractions(request):
    """搜索景点的 API 视图函数"""
    try:
        query = request.GET.get('q', '')
        if len(query) < 2:
            return JsonResponse({'error': '搜索关键词太短'}, status=400)
        
        attractions = Attraction.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(epithet__icontains=query)
        ).values('id', 'name')[:10]  # 限制返回10个结果
        
        return JsonResponse(list(attractions), safe=False)
        
    except Exception as e:
        logger.error(f"搜索景点时发生错误: {str(e)}")
        return JsonResponse({
            'error': '搜索失败，请稍后重试',
            'details': str(e)
        }, status=500)

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        email = request.POST["email"]
        
        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            return render(request, "TourismSystem/register.html", {
                "message": "用户名已存在"
            })
        
        # 创建新用户
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "TourismSystem/register.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))

def attraction_list(request):
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
        "sort": sort
    })

def diary_list(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
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
    return render(request, "TourismSystem/diary_list.html", {
        "page_obj": page_obj,
        "sort": sort,
        "keyword": keyword,
    })

def diary_create(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    if request.method == "POST":
        form = DiaryForm(request.POST, request.FILES)
        if form.is_valid():
            diary = form.save(commit=False)
            diary.author = request.user
            diary.save()
            return redirect('diary_detail', diary_id=diary.id)
    else:
        form = DiaryForm()
    
    return render(request, "TourismSystem/diary_form.html", {
        "form": form,
        "title": "创建日记"
    })

def diary_edit(request, diary_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    diary = get_object_or_404(Diary, id=diary_id, author=request.user)
    
    if request.method == "POST":
        form = DiaryForm(request.POST, request.FILES, instance=diary)
        if form.is_valid():
            diary = form.save()
            return redirect('diary_detail', diary_id=diary.id)
    else:
        form = DiaryForm(instance=diary)
    
    return render(request, "TourismSystem/diary_form.html", {
        "form": form,
        "title": "编辑日记"
    })

def diary_delete(request, diary_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    diary = get_object_or_404(Diary, id=diary_id, author=request.user)
    
    if request.method == "POST":
        diary.delete()
        return redirect('diary_list')
    
    return render(request, "TourismSystem/diary_confirm_delete.html", {
        "diary": diary
    })

def profile(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/profile.html")

def profile_edit(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/profile_edit.html")

def change_password(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/change_password.html")

def change_avatar(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/change_avatar.html")

def delete_account(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request, "TourismSystem/delete_account.html")

def about(request):
    return render(request, "TourismSystem/about.html")

def contact(request):
    return render(request, "TourismSystem/contact.html")

def help(request):
    return render(request, "TourismSystem/help.html")

def terms(request):
    return render(request, "TourismSystem/terms.html")

def privacy(request):
    return render(request, "TourismSystem/privacy.html")

def sitemap(request):
    return render(request, "TourismSystem/sitemap.html")

def robots(request):
    return render(request, "TourismSystem/robots.html")

def not_found(request):
    return render(request, "TourismSystem/404.html")

def server_error(request):
    return render(request, "TourismSystem/500.html")

@require_http_methods(["POST"])
def search_places(request):
    """搜索景点的视图函数"""
    try:
        query = request.POST.get('q', '')
        sort_by = request.POST.get('sort_by', 'popularity')
        
        if not query:
            return JsonResponse({
                'code': 400,
                'msg': '搜索关键词不能为空'
            })
        
        # 构建搜索关键词列表
        search_terms = query.split()
        search_query = Q()
        
        # 对每个搜索词构建查询条件
        for term in search_terms:
            term_query = Q(name__icontains=term) | Q(category__icontains=term) | Q(keywords__icontains=term)
            search_query |= term_query
        
        # 添加完整匹配的查询条件
        search_query |= Q(name__icontains=query) | Q(category__icontains=query) | Q(keywords__icontains=query)
        
        # 在数据库中搜索
        attractions = Attraction.objects.filter(search_query).distinct()
        
        # 根据排序方式排序
        if sort_by == 'rating':
            attractions = attractions.order_by('-rating', '-rating_count')
        else:  # 默认按热度排序
            attractions = attractions.order_by('-popularity')
        
        # 只返回前10个结果
        attractions = attractions[:10]
        
        # 格式化结果
        formatted_results = []
        for attraction in attractions:
            formatted_results.append({
                'id': attraction.id,
                'name': attraction.name,
                'url': f'/TourismSystem/attractions/{attraction.id}/'
            })
        
        return JsonResponse({
            'code': 200,
            'data': formatted_results
        })
        
    except Exception as e:
        logger.error(f"搜索景点时发生错误: {str(e)}")
        return JsonResponse({
            'code': 500,
            'msg': '搜索失败，请稍后重试'
        })
