import random
from django.contrib.auth.models import User
from TourismSystem.models import Attraction, Diary, DiaryComment, DiaryLike
from django.core.files.base import ContentFile
import urllib.request

# 真实感景点数据（名称、简介、图片URL、类别、关键字）
spots = [
    {
        "name": "北京故宫",
        "epithet": "中国明清两代的皇家宫殿，世界上现存规模最大、保存最为完整的木质结构古建筑之一。",
        "cover_url": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80",
        "category": "history",
        "keywords": "历史,文化,古迹"
    },
    {
        "name": "上海外滩",
        "epithet": "外滩是上海最具代表性的景观之一，沿江矗立着多座风格各异的历史建筑。",
        "cover_url": "https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=800&q=80",
        "category": "city",
        "keywords": "城市,江景,建筑"
    },
    {
        "name": "杭州西湖",
        "epithet": "西湖以其秀丽的湖光山色和众多的名胜古迹闻名于世，是中国著名的旅游胜地。",
        "cover_url": "https://images.unsplash.com/photo-1506089676908-3592f7389d4d?auto=format&fit=crop&w=800&q=80",
        "category": "nature",
        "keywords": "湖泊,自然,风景"
    },
    {
        "name": "成都宽窄巷子",
        "epithet": "宽窄巷子是成都最具历史文化气息的街区之一，融合了老成都的生活与现代时尚。",
        "cover_url": "https://images.unsplash.com/photo-1519125323398-675f0ddb6308?auto=format&fit=crop&w=800&q=80",
        "category": "city",
        "keywords": "美食,文化,休闲"
    },
    {
        "name": "广州塔",
        "epithet": "广州塔又称小蛮腰，是广州的地标性建筑，夜景尤为迷人。",
        "cover_url": "https://images.unsplash.com/photo-1465101046530-73398c7f28ca?auto=format&fit=crop&w=800&q=80",
        "category": "city",
        "keywords": "地标,建筑,夜景"
    },
    {
        "name": "南京大学鼓楼校区",
        "epithet": "南京大学鼓楼校区历史悠久，环境优美，是中国著名高等学府之一。",
        "cover_url": "https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80",
        "category": "campus",
        "keywords": "校园,学府,历史"
    },
    {
        "name": "巴黎埃菲尔铁塔",
        "epithet": "埃菲尔铁塔是法国巴黎的标志性建筑，也是世界著名旅游胜地。",
        "cover_url": "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=800&q=80",
        "category": "city",
        "keywords": "地标,建筑,浪漫"
    },
    {
        "name": "纽约中央公园",
        "epithet": "中央公园是纽约市中心的一片绿洲，市民和游客休闲娱乐的好去处。",
        "cover_url": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=800&q=80",
        "category": "nature",
        "keywords": "公园,自然,休闲"
    },
    {
        "name": "东京浅草寺",
        "epithet": "浅草寺是东京最古老、最著名的寺庙之一，香火鼎盛，游客众多。",
        "cover_url": "https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=800&q=80",
        "category": "history",
        "keywords": "寺庙,文化,历史"
    },
    {
        "name": "悉尼歌剧院",
        "epithet": "悉尼歌剧院以其独特的帆船造型闻名，是澳大利亚的文化地标。",
        "cover_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
        "category": "city",
        "keywords": "地标,建筑,艺术"
    }
]

# 日记内容模板
diary_templates = [
    "今天和朋友一起游览了{spot}，{desc}。最喜欢这里的{feature}，拍了很多照片，感觉非常棒！",
    "第一次来到{spot}，{desc}。这里的{feature}让我印象深刻，下次还想再来。",
    "在{spot}度过了愉快的一天，{desc}。推荐大家来体验一下{feature}！",
    "和家人一起参观了{spot}，{desc}。{feature}真的很有特色，值得一看。",
    "来{spot}打卡，{desc}。{feature}是这里的亮点，强烈推荐！"
]
features = ["风景", "建筑", "美食", "文化氛围", "夜景", "历史感", "自然环境", "人文气息"]

# 评论模板
comment_templates = [
    "写得真好，感觉身临其境！",
    "下次我也要去看看！",
    "照片拍得很美，内容很实用。",
    "感谢分享，攻略很详细！",
    "这里真的值得一去！"
]

# 用户昵称模板
user_nicknames = [
    "旅行者小明", "摄影师小李", "背包客小王", "大学生小赵", "美食家小陈",
    "文艺青年小刘", "探险家小孙", "爱拍照的小周", "历史控小吴", "自然爱好者小郑",
    "小杨", "小何", "小林", "小唐", "小马", "小徐", "小高", "小罗", "小冯", "小邓",
    "小曹", "小潘", "小袁", "小蒋", "小杜", "小丁", "小沈", "小魏", "小许", "小宋",
    "小叶", "小贾", "小邵", "小彭", "小谭", "小姚", "小卢", "小程", "小汪", "小姜",
    "小石", "小傅", "小汤", "小白", "小金", "小熊", "小江", "小邹", "小龚", "小赖"
]

def get_image_from_url(url, name):
    try:
        img_bytes = urllib.request.urlopen(url).read()
        return ContentFile(img_bytes, name=f'{name}.jpg')
    except Exception as e:
        print(f"下载图片失败: {url}, 错误: {e}")
        return None

# 生成用户
user_objs = []
for i, nickname in enumerate(user_nicknames):
    username = f'user{i+1}'
    user, created = User.objects.get_or_create(username=username, defaults={'first_name': nickname})
    if created:
        user.set_password('test123456')
        user.save()
    user_objs.append(user)

# 生成景点和日记
for idx, spot in enumerate(spots):
    cover = get_image_from_url(spot["cover_url"], f"attraction_{idx+1}")
    attraction = Attraction.objects.create(
        name=spot["name"],
        category=spot["category"],
        keywords=spot["keywords"],
        epithet=spot["epithet"],
        popularity=random.randint(1000, 10000),
        rating=0,
        rating_count=0,
        cover=cover,
        latitude=round(random.uniform(30, 40), 6),
        longitude=round(random.uniform(110, 120), 6)
    )
    # 生成日记
    for j in range(5):
        author = user_objs[(idx*5+j) % len(user_objs)]
        template = random.choice(diary_templates)
        feature = random.choice(features)
        content = template.format(
            spot=spot["name"],
            desc=spot["epithet"],
            feature=feature
        )
        diary_image = cover  # 用景点封面图作为日记图片（如需不同可换成其它图片API）
        diary = Diary.objects.create(
            title=f"{spot['name']}游记{j+1}",
            content=content,
            image=diary_image,
            author=author,
            attraction=attraction,
            rating=random.randint(4, 5),
            popularity=random.randint(50, 500),
        )
        # 生成评论
        for k in range(3):
            comment_user = random.choice(user_objs)
            DiaryComment.objects.create(
                diary=diary,
                author=comment_user,
                content=random.choice(comment_templates)
            )
        # 生成点赞
        like_users = random.sample(user_objs, 5)
        for like_user in like_users:
            DiaryLike.objects.get_or_create(diary=diary, user=like_user)
    # 更新景点评分
    diaries = attraction.diaries.all()
    if diaries.exists():
        total_score = sum([d.rating for d in diaries])
        attraction.rating = round(total_score / diaries.count(), 1)
        attraction.rating_count = diaries.count()
        attraction.save()

print("高质量测试数据生成完毕！")