import json

def update_diaries():
    # 读取diaries.json
    with open('TourismSystem/static/TourismSystem/data/diaries.json', 'r', encoding='utf-8') as f:
        diaries = json.load(f)
    
    # 更新diaries中的placeId
    updated_count = 0
    for diary in diaries:
        old_place_id = diary.get('placeId')
        if old_place_id:
            # 提取数字部分并补零
            num_part = old_place_id.split('_')[-1]
            new_place_id = f"place_{num_part.zfill(3)}"
            diary['placeId'] = new_place_id
            updated_count += 1
    
    # 保存更新后的diaries.json
    with open('TourismSystem/static/TourismSystem/data/diaries.json', 'w', encoding='utf-8') as f:
        json.dump(diaries, f, ensure_ascii=False, indent=2)
    
    print(f"更新完成! 共更新了 {updated_count} 条日记的placeId")

if __name__ == '__main__':
    update_diaries() 