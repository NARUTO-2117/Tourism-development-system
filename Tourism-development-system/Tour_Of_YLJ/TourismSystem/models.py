from django.db import models
from django.contrib.auth.models import User

class Attraction(models.Model):
    CATEGORY_CHOICES = [
        ('nature', '自然景观'),
        ('history', '历史古迹'),
        ('city', '城市地标'),
        ('campus', '校园'),
        ('teaching', '教学楼'),
        ('office', '办公楼'),
        ('dorm', '宿舍楼'),
        ('shop', '商店'),
        ('restaurant', '饭店'),
        ('toilet', '洗手间'),
        ('library', '图书馆'),
        ('canteen', '食堂'),
        ('supermarket', '超市'),
        ('cafe', '咖啡馆'),
        # 可扩展
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    keywords = models.CharField(max_length=200, blank=True, help_text="用逗号分隔")
    epithet = models.CharField(max_length=200, blank=True)
    popularity = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    cover = models.ImageField(upload_to='attraction_covers/', default='TourismSystem/images/default.jpg')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        unique_together = ('name', 'parent')

    def __str__(self):
        return self.name

class Diary(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='diary_images/')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name='diaries')
    rating = models.IntegerField()  # 1-5星
    popularity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    can_modify_rating = models.BooleanField(default=True)  # 限制评分修改一次

    class Meta:
        unique_together = ('author', 'attraction')

    def __str__(self):
        return self.title

class DiaryComment(models.Model):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class DiaryLike(models.Model):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('diary', 'user')