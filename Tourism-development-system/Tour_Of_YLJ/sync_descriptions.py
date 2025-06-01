import os
import django
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tour_Of_YLJ.settings')
django.setup()

from TourismSystem.models import Attraction

def sync_descriptions():
    # 读取places.json文件
    with open('TourismSystem/static/TourismSystem/data/places.json', 'r', encoding='utf-8') as f:
        places_data = json.load(f)
    
    # 用 name 做映射
    name_to_description = {place['name']: place.get('description', '') for place in places_data}
    
    # 更新数据库中的景点描述
    success_count = 0
    fail_count = 0
    
    for attraction in Attraction.objects.all():
        desc = name_to_description.get(attraction.name)
        if desc is not None:
            attraction.description = desc
            attraction.save()
            success_count += 1
        else:
            print(f"未找到景点 {attraction.name} 的描述")
            fail_count += 1
    
    print(f"同步完成！成功: {success_count}，失败: {fail_count}")

if __name__ == '__main__':
    sync_descriptions() 