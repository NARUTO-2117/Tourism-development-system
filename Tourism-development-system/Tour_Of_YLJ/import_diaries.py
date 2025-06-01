import os
import sys
import django
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tour_Of_YLJ.settings')
django.setup()

from TourismSystem.models import Diary, Attraction, User

def import_diaries():
    # 读取diaries.json文件
    with open('TourismSystem/static/TourismSystem/data/diaries.json', 'r', encoding='utf-8') as f:
        diaries_data = json.load(f)

    # 读取places.json文件以获取景点名称映射
    with open('TourismSystem/static/TourismSystem/data/places.json', 'r', encoding='utf-8') as f:
        places_data = json.load(f)
        place_id_to_name = {place['id']: place['name'] for place in places_data}

    success_count = 0
    fail_count = 0

    for diary in diaries_data:
        try:
            # 获取作者
            author = User.objects.get(id=diary['authorId'].split('_')[1])

            # 获取景点
            place_id = diary['placeId']
            place_name = place_id_to_name.get(place_id)
            if not place_name:
                print(f"找不到景点ID: {place_id}")
                continue
            attraction = Attraction.objects.get(name=place_name)

            # 创建或更新日记
            diary_obj, created = Diary.objects.update_or_create(
                diary_id=diary['id'],
                defaults={
                    'title': diary['title'],
                    'content': diary['content'],
                    'image': attraction.cover,  # 使用景点的封面图片
                    'author': author,
                    'attraction': attraction,
                    'rating': diary['rating'],
                    'rating_count': diary['ratingCount'],  # 使用ratingCount字段
                    'popularity': diary['clickCount'],
                    'created_at': datetime.fromisoformat(diary['createdAt'].replace('Z', '+00:00')),
                    'tags': ','.join(diary['tags']) if diary.get('tags') else ''
                }
            )
            success_count += 1
        except Exception as e:
            print(f"导入失败: {diary['id']}，原因: {str(e)}")
            fail_count += 1

    print(f"\n导入完成，成功: {success_count}，失败: {fail_count}")

if __name__ == '__main__':
    import_diaries() 