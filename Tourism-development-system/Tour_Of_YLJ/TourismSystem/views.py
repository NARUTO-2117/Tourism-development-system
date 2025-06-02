from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Attraction, Diary, DiaryComment, DiaryLike, Food, FoodReview
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied
from .forms import DiaryForm, UserRegistrationForm
from django.db.models import Q, F, Count, Avg
from django.core.paginator import Paginator
from django.views import View
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os
import json
from django.core.cache import cache
import logging
import base64
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .food_algorithms import FoodFinder, FoodSorter
import random

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
    
    # 类别映射字典
    category_mapping = {
        'natural': 'nature',  # 将"自然景观"映射到数据库中的"nature"
    }
    
    attractions = Attraction.objects.all()
    if category:
        # 使用映射后的类别值进行筛选
        db_category = category_mapping.get(category, category)
        attractions = attractions.filter(category=db_category)
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
    location = request.GET.get("location", "")  # 新增景点地址搜索
    
    # 获取所有日记，并预加载相关数据
    diaries = Diary.objects.select_related('author', 'attraction')
    
    # 构建搜索条件
    if keyword or location:
        query = Q()
        if keyword:
            query |= Q(title__icontains=keyword)
            # 对于压缩的内容，先解压再搜索
            for diary in diaries:
                try:
                    if diary.content:
                        decompressed_content = diary.get_content()
                        if keyword.lower() in decompressed_content.lower():
                            query |= Q(id=diary.id)
                except:
                    continue
        if location:
            query &= Q(attraction__name__icontains=location)
        diaries = diaries.filter(query)
    
    # 应用排序
    if sort == "rating":
        diaries = diaries.order_by("-rating", "-created_at")
    elif sort == "time":
        diaries = diaries.order_by("-created_at")
    else:  # popularity
        diaries = diaries.order_by("-popularity", "-created_at")
    
    # 分页
    paginator = Paginator(diaries, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # 获取所有景点名称用于搜索建议
    attractions = Attraction.objects.values_list('name', flat=True)
    
    return render(request, "TourismSystem/log.html", {
        "page_obj": page_obj,
        "sort": sort,
        "keyword": keyword,
        "location": location,
        "attractions": list(attractions),  # 转换为列表以便在模板中使用
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

    # 景点查询和展示功能
    sort = request.GET.get("sort", "popularity")  # 默认按热度
    category = request.GET.get("category", "")
    keyword = request.GET.get("keyword", "")
    
    # 类别映射字典
    category_mapping = {
        'natural': 'nature',  # 将"自然景观"映射到数据库中的"nature"
    }
    
    attractions = Attraction.objects.all()
    if category:
        # 使用映射后的类别值进行筛选
        db_category = category_mapping.get(category, category)
        attractions = attractions.filter(category=db_category)
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
    
    context = {
        "hot_attractions": hot_attractions,
        "spots_1_list": city_rank_list,
        "current_sort": sort_by,  # 传递当前排序方式到模板
        "page_obj": page_obj,
        "categories": categories,
        "current_category": category,
        "current_keyword": keyword,
        "sort": sort
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
    """景点详情页面，添加了美食推荐功能"""
    # 获取景点信息
    spot = get_object_or_404(Attraction, id=spot_id)
    
    # 获取景点评分信息
    avg_rating = Diary.objects.filter(attraction=spot).aggregate(Avg('rating'))
    if avg_rating['rating__avg'] is not None:
        spot_rating = round(avg_rating['rating__avg'], 1)
    else:
        spot_rating = 0
    
    # 获取相关日记
    diaries = Diary.objects.filter(attraction=spot).order_by('-created_at')[:5]
    
    # 获取景点附近的美食，按热度排序
    nearby_foods = Food.objects.filter(attraction=spot).order_by('-popularity')[:5]
    
    return render(request, "TourismSystem/attraction_detail.html", {
        "spot": spot,
        "spot_rating": spot_rating,
        "diaries": diaries,
        "nearby_foods": nearby_foods,  # 添加附近美食数据
    })

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
        logger.debug(f"尝试解压内容: {compressed_content[:50]}...") # 记录前50个字符
        # 将base64字符串转换回字节
        compressed_bytes = base64.b64decode(compressed_content)
        logger.debug(f"Base64 解码后的字节: {compressed_bytes[:50]}...") # 记录前50个字节
        # 使用zlib解压
        decompressed = zlib.decompress(compressed_bytes)
        logger.debug(f"Zlib 解压后的字节: {decompressed[:50]}...") # 记录前50个字节
        # 将解压后的字节转换回字符串
        decoded_content = decompressed.decode('utf-8')
        logger.debug(f"UTF-8 解码后的字符串: {decoded_content[:50]}...") # 记录前50个字符
        return decoded_content
    except Exception as e:
        logger.error(f"解压内容时发生错误: {str(e)}")
        return compressed_content

@login_required
def upload_diary(request, spot_id):
    """上传旅游日记的视图函数"""
    try:
        attraction = get_object_or_404(Attraction, id=spot_id)
        user = request.user

        # 检查是否已上传过日记
        existing_diary = Diary.objects.filter(author=user, attraction=attraction).first()
        if existing_diary and not existing_diary.can_modify_rating:
            messages.error(request, "您已上传过该景点的日记且评分已修改过，不能再次上传。")
            return render(request, "TourismSystem/diary_upload.html", {
                "attraction": attraction,
                "diary": existing_diary,
                "form": DiaryForm(instance=existing_diary)
            })

        if request.method == "POST":
            logger.info(f"Received diary upload request for attraction {spot_id} from user {user.username}")
            form = DiaryForm(request.POST, request.FILES, instance=existing_diary if existing_diary else None)
            
            if form.is_valid():
                try:
                    diary = form.save(commit=False)
                    diary.author = user
                    diary.attraction = attraction
                    
                    # 评分只能修改一次
                    if existing_diary and existing_diary.can_modify_rating:
                        diary.can_modify_rating = False

                    # 保存日记（内容会在save方法中自动压缩）
                    diary.save()
                    logger.info(f"Successfully saved diary ID: {diary.id}")

                    # 更新景点评分
                    try:
                        diaries = Diary.objects.filter(attraction=attraction)
                        if diaries.exists():
                            total_score = sum([d.rating for d in diaries])
                            attraction.rating = round(total_score / diaries.count(), 1)
                            attraction.rating_count = diaries.count()
                        else:
                            attraction.rating = 0
                            attraction.rating_count = 0
                        attraction.save()
                        logger.info(f"Updated attraction rating for ID: {attraction.id}")
                    except Exception as e:
                        logger.error(f"Error updating attraction rating: {e}")
                        messages.warning(request, "日记已保存，但更新景点评分时出现错误。")

                    messages.success(request, "日记上传成功！")
                    return redirect('diary_detail', diary_id=diary.id)

                except Exception as e:
                    logger.error(f"Error saving diary: {e}", exc_info=True)
                    messages.error(request, f"保存日记时发生错误: {str(e)}")
                    return render(request, "TourismSystem/diary_upload.html", {
                        "form": form,
                        "attraction": attraction,
                        "diary": existing_diary,
                    })
            else:
                logger.warning(f"Form validation failed: {form.errors}")
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                return render(request, "TourismSystem/diary_upload.html", {
                    "form": form,
                    "attraction": attraction,
                    "diary": existing_diary,
                })

        else:  # GET request
            form = DiaryForm(instance=existing_diary if existing_diary else None)
            if existing_diary:
                existing_diary.content = existing_diary.get_content()
            return render(request, "TourismSystem/diary_upload.html", {
                "form": form,
                "attraction": attraction,
                "diary": existing_diary
            })

    except Exception as e:
        logger.error(f"Unexpected error in upload_diary: {e}", exc_info=True)
        messages.error(request, "发生意外错误，请稍后重试。")
        return redirect('index')

def diary_detail(request, diary_id):
    diary = get_object_or_404(Diary, id=diary_id)
    # 获取解压后的内容
    diary.content = diary.get_content()
    # 获取日记的所有评论
    comments = DiaryComment.objects.filter(diary=diary).order_by('-created_at')
    
    return render(request, "TourismSystem/diary_detail.html", {
        "diary": diary,
        "comments": comments,
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
                likes_count=Count('likes'),
                comments_count=Count('diary_comments')
            ).annotate(
                popularity_score=F('likes_count') * 0.4 + F('comments_count') * 0.3 + F('views') * 0.3
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
                    'content': diary.content if diary.content else '',
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
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, "注册成功！欢迎加入我们。")
                return redirect('index')
            except Exception as e:
                logger.error(f"注册失败: {str(e)}")
                messages.error(request, "注册过程中发生错误，请稍后重试。")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, "TourismSystem/register.html", {
        "form": form,
        "title": "注册"
    })

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
        
        # 定义常见缩写映射
        common_abbreviations = {
            '北邮': '北京邮电大学',
            '北大': '北京大学',
            '清华': '清华大学',
            '人大': '中国人民大学',
            '北航': '北京航空航天大学',
            '北理': '北京理工大学',
            '北师': '北京师范大学',
            '北外': '北京外国语大学',
            '北交': '北京交通大学',
            '北科': '北京科技大学',
            '北工': '北京工业大学',
            '北林': '北京林业大学',
            '北农': '北京农业大学',
            '北医': '北京大学医学部',
            '北影': '北京电影学院',
            '北舞': '北京舞蹈学院',
            '北音': '北京音乐学院',
            '北体': '北京体育大学',
            '北语': '北京语言大学',
            '北化': '北京化工大学'
        }
        
        # 构建搜索关键词列表
        search_terms = [query]
        
        # 检查是否匹配缩写
        for abbr, full in common_abbreviations.items():
            if abbr in query:
                search_terms.append(query.replace(abbr, full))
        
        # 构建查询条件
        search_query = Q()
        for term in search_terms:
            term_query = Q(name__icontains=term) | Q(category__icontains=term) | Q(keywords__icontains=term)
            search_query |= term_query
        
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

# 美食推荐相关视图
@login_required
def food_recommendation(request):
    """美食推荐页面"""
    # 获取筛选和排序参数
    sort_by = request.GET.get('sort_by', 'popularity')  # 默认按热度排序
    cuisine = request.GET.get('cuisine', '')  # 默认不筛选菜系
    search_query = request.GET.get('query', '')  # 搜索关键词
    attraction_id = request.GET.get('attraction_id', None)  # 景点ID
    
    # 使用FoodFinder进行搜索和筛选
    foods = FoodFinder.search_foods(search_query, cuisine)
    
    # 如果提供了景点ID，筛选该景点附近的美食
    if attraction_id:
        foods = FoodFinder.filter_by_attraction(foods, attraction_id)
    
    # 获取用户位置（如果提供）
    user_lat = request.GET.get('lat', None)
    user_lon = request.GET.get('lon', None)
    if user_lat and user_lon:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except ValueError:
            user_lat = user_lon = None
    
    # 使用优化的算法获取前10个美食
    top_foods = FoodSorter.get_top_k_foods(foods, 10, sort_by, user_lat, user_lon)
    
    # 如果结果不足10个，则使用普通排序获取所有结果
    if len(top_foods) < 10:
        top_foods = FoodSorter.sort_foods(foods, sort_by, user_lat, user_lon)
    
    # 分页
    paginator = Paginator(top_foods, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # 获取所有菜系选项
    cuisine_choices = Food.CUISINE_CHOICES
    
    # 获取所有景点
    attractions = Attraction.objects.all()
    
    return render(request, "TourismSystem/food_recommendation.html", {
        "page_obj": page_obj,
        "sort_by": sort_by,
        "cuisine": cuisine,
        "cuisine_choices": cuisine_choices,
        "query": search_query,
        "attraction_id": attraction_id,
        "attractions": attractions,
    })

@login_required
def food_detail(request, food_id):
    """美食详情页面"""
    food = get_object_or_404(Food, id=food_id)
    
    # 获取用户之前的评价（如果有）
    user_review = FoodReview.objects.filter(food=food, user=request.user).first()
    
    # 获取所有评价
    reviews = FoodReview.objects.filter(food=food).select_related('user').order_by('-created_at')
    
    # 处理提交评价
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content', '')
        
        if rating:
            try:
                rating = float(rating)
                # 确保评分在1-5之间
                rating = max(1.0, min(5.0, rating))
                
                # 创建或更新评价
                if user_review:
                    user_review.rating = rating
                    user_review.content = content
                    user_review.save()
                else:
                    user_review = FoodReview.objects.create(
                        food=food,
                        user=request.user,
                        rating=rating,
                        content=content
                    )
                
                # 更新美食的平均评分
                avg_rating = FoodReview.objects.filter(food=food).aggregate(Avg('rating'))['rating__avg'] or 0.0
                food.rating = avg_rating
                food.rating_count = FoodReview.objects.filter(food=food).count()
                food.save()
                
                messages.success(request, '评价已提交')
                return redirect('food_detail', food_id=food.id)
            except ValueError:
                messages.error(request, '无效的评分')
    
    # 获取相似美食推荐
    similar_foods = Food.objects.filter(
        Q(cuisine=food.cuisine) | Q(restaurant=food.restaurant)
    ).exclude(id=food.id).order_by('-popularity')[:5]
    
    return render(request, "TourismSystem/food_detail.html", {
        "food": food,
        "user_review": user_review,
        "reviews": reviews,
        "similar_foods": similar_foods,
    })

@require_http_methods(["GET"])
def search_foods(request):
    """API端点：搜索美食"""
    query = request.GET.get('query', '')
    cuisine = request.GET.get('cuisine', '')
    attraction_id = request.GET.get('attraction_id', None)
    sort_by = request.GET.get('sort_by', 'popularity')
    limit = int(request.GET.get('limit', 10))
    
    # 搜索美食
    foods = FoodFinder.search_foods(query, cuisine)
    
    # 筛选景点
    if attraction_id:
        foods = FoodFinder.filter_by_attraction(foods, attraction_id)
    
    # 获取用户位置
    user_lat = request.GET.get('lat', None)
    user_lon = request.GET.get('lon', None)
    if user_lat and user_lon:
        try:
            user_lat = float(user_lat)
            user_lon = float(user_lon)
        except ValueError:
            user_lat = user_lon = None
    
    # 获取前N个结果
    top_foods = FoodSorter.get_top_k_foods(foods, limit, sort_by, user_lat, user_lon)
    
    # 格式化结果
    results = []
    for food in top_foods:
        results.append({
            'id': food.id,
            'name': food.name,
            'restaurant': food.restaurant,
            'cuisine': food.get_cuisine_display(),
            'price': float(food.price),
            'rating': food.rating,
            'rating_count': food.rating_count,
            'image_url': food.image.url if food.image else None,
            'attraction_id': food.attraction_id,
            'attraction_name': food.attraction.name,
        })
    
    return JsonResponse({
        'results': results,
        'total': len(foods),
        'query': query,
        'cuisine': cuisine,
    })

@login_required
def add_food_review(request, food_id):
    """添加美食评价"""
    food = get_object_or_404(Food, id=food_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content', '')
        
        if rating:
            try:
                rating = float(rating)
                # 确保评分在1-5之间
                rating = max(1.0, min(5.0, rating))
                
                # 创建或更新评价
                review, created = FoodReview.objects.update_or_create(
                    food=food,
                    user=request.user,
                    defaults={
                        'rating': rating,
                        'content': content
                    }
                )
                
                # 更新美食的平均评分
                avg_rating = FoodReview.objects.filter(food=food).aggregate(Avg('rating'))['rating__avg'] or 0.0
                food.rating = avg_rating
                food.rating_count = FoodReview.objects.filter(food=food).count()
                food.save()
                
                messages.success(request, '评价已提交')
            except ValueError:
                messages.error(request, '无效的评分')
    
    return redirect('food_detail', food_id=food.id)

# 伪造美食数据
@login_required
def load_demo_foods(request):
    # 清空现有数据
    Food.objects.all().delete()
    
    # 获取或创建三个食堂
    student_canteen = Attraction.objects.get_or_create(name='学生食堂')[0]
    flavor_canteen = Attraction.objects.get_or_create(name='风味食堂')[0]
    comprehensive_canteen = Attraction.objects.get_or_create(name='综合食堂')[0]
    
    # 伪造美食数据
    foods = [
        {
            'name': '红烧肉',
            'restaurant': '学生食堂',
            'attraction': student_canteen,
            'price': 15.0,
            'cuisine': 'chinese',
            'description': '经典红烧肉，肥而不腻，入口即化。',
            'keywords': '红烧肉,经典,学生食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
        {
            'name': '麻辣香锅',
            'restaurant': '风味食堂',
            'attraction': flavor_canteen,
            'price': 20.0,
            'cuisine': 'chinese',
            'description': '麻辣香锅，香辣可口，配料丰富。',
            'keywords': '麻辣香锅,香辣,风味食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
        {
            'name': '炸鸡',
            'restaurant': '综合食堂',
            'attraction': comprehensive_canteen,
            'price': 18.0,
            'cuisine': 'western',
            'description': '外酥里嫩，香脆可口。',
            'keywords': '炸鸡,香脆,综合食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
        {
            'name': '牛肉面',
            'restaurant': '学生食堂',
            'attraction': student_canteen,
            'price': 12.0,
            'cuisine': 'chinese',
            'description': '牛肉面，汤鲜味美，面条筋道。',
            'keywords': '牛肉面,汤鲜,学生食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
        {
            'name': '寿司',
            'restaurant': '风味食堂',
            'attraction': flavor_canteen,
            'price': 25.0,
            'cuisine': 'japanese',
            'description': '新鲜寿司，口感细腻。',
            'keywords': '寿司,新鲜,风味食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
        {
            'name': '披萨',
            'restaurant': '综合食堂',
            'attraction': comprehensive_canteen,
            'price': 30.0,
            'cuisine': 'western',
            'description': '意式披萨，芝士浓郁，配料丰富。',
            'keywords': '披萨,芝士,综合食堂',
            'popularity': random.randint(80, 100),
            'latitude': 39.9600,
            'longitude': 116.3600,
        },
    ]
    
    for food_data in foods:
        Food.objects.create(**food_data)
    
    return redirect('food_recommendation')
