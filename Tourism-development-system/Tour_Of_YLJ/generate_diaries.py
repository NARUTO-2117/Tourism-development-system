import json
import random
from datetime import datetime, timedelta

# 读取景点数据
with open('TourismSystem/static/TourismSystem/data/places.json', 'r', encoding='utf-8') as f:
    places = json.load(f)

author_ids = [f'user_{str(i).zfill(3)}' for i in range(1, 11)]
title_templates = [
    '畅游{place}', '打卡{place}', '探秘{place}', '{place}一日游', '难忘的{place}之旅', '美丽的{place}', '{place}游记'
]
content_templates = [
    '今天参观了{place}，感受到了{feature}，非常值得一来！',
    '{place}的{feature}让我印象深刻，下次还想再来。',
    '和朋友一起去了{place}，体验了{feature}，收获满满。',
    '在{place}度过了愉快的一天，{feature}真的很棒！',
    '推荐大家来{place}，尤其是这里的{feature}。'
]

diaries = []
diary_id = 1
now = datetime.now()

for place in places:
    place_id = place['id']
    place_name = place['name']
    features = place.get('features', ['风景优美'])
    image = place.get('image', '')
    place_type = place.get('type', '景点')
    for i in range(3):
        diary = {
            'id': f'diary_{str(diary_id).zfill(3)}',
            'title': random.choice(title_templates).format(place=place_name),
            'content': random.choice(content_templates).format(place=place_name, feature=random.choice(features)),
            'placeId': place_id,
            'authorId': random.choice(author_ids),
            'clickCount': random.randint(0, 100),
            'rating': round(random.uniform(3.0, 5.0), 1),
            'ratingCount': random.randint(1, 20),
            'createdAt': (now - timedelta(days=random.randint(0, 365))).isoformat() + 'Z',
            'images': [image] if image else [],
            'videos': [],
            'tags': [place_type] + features[:2]
        }
        diaries.append(diary)
        diary_id += 1

with open('TourismSystem/static/TourismSystem/data/diaries.json', 'w', encoding='utf-8') as f:
    json.dump(diaries, f, ensure_ascii=False, indent=2)

print(f'已为{len(places)}个景点生成{len(diaries)}条日记，并覆盖diaries.json') 