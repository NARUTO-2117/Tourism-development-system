from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import zlib
import base64
import logging

logger = logging.getLogger(__name__)

class Attraction(models.Model):
    CATEGORY_CHOICES = [
        ('', '全部类别'),
        ('natural', '自然景观'),
        ('campus', '校园'),
        ('history', '历史古迹'),
        ('city', '城市地标'),
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
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='')
    keywords = models.CharField(max_length=200, blank=True, help_text="用逗号分隔")
    epithet = models.CharField(max_length=200, blank=True)
    popularity = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    cover = models.ImageField(upload_to='attraction_covers/', default='TourismSystem/images/default.jpg')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True, default='')  # 新增景点介绍字段

    class Meta:
        unique_together = ('name', 'parent')

    def __str__(self):
        return self.name

class Food(models.Model):
    """美食模型，用于存储北邮校内外的美食信息"""
    CUISINE_CHOICES = [
        ('', '全部菜系'),
        ('sichuan', '川菜'),
        ('cantonese', '粤菜'),
        ('hunan', '湘菜'),
        ('jiangsu', '苏菜'),
        ('shandong', '鲁菜'),
        ('zhejiang', '浙菜'),
        ('anhui', '徽菜'),
        ('fujian', '闽菜'),
        ('fast_food', '快餐'),
        ('snack', '小吃'),
        ('hotpot', '火锅'),
        ('bbq', '烧烤'),
        ('dessert', '甜点'),
        ('drink', '饮品'),
        ('western', '西餐'),
        ('japanese', '日料'),
        ('korean', '韩餐'),
        ('southeast_asian', '东南亚菜'),
        ('other', '其他'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='美食名称')
    restaurant = models.CharField(max_length=100, verbose_name='餐厅/窗口名称', default='学生食堂')
    cuisine = models.CharField(max_length=20, choices=CUISINE_CHOICES, default='', verbose_name='菜系')
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='价格')
    popularity = models.IntegerField(default=0, verbose_name='热度')
    rating = models.FloatField(default=0.0, verbose_name='评分')
    rating_count = models.IntegerField(default=0, verbose_name='评分数量')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    image = models.ImageField(upload_to='food_images/', default='TourismSystem/images/default_food.jpg', verbose_name='图片')
    
    # 位置信息
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name='foods', verbose_name='所属景点')
    latitude = models.FloatField(verbose_name='纬度')
    longitude = models.FloatField(verbose_name='经度')
    
    # 其他信息
    keywords = models.CharField(max_length=200, blank=True, help_text="用逗号分隔", verbose_name='关键词')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        ordering = ['-popularity']
        verbose_name = '美食'
        verbose_name_plural = '美食'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['restaurant']),
            models.Index(fields=['cuisine']),
            models.Index(fields=['popularity']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.restaurant}"
    
    def calculate_distance(self, latitude, longitude):
        """计算与给定位置的距离（简化版，仅作演示）"""
        # 使用欧几里得距离计算（实际应用中可使用更准确的地球距离计算方法）
        if latitude is None or longitude is None:
            return float('inf')  # 返回无穷大，表示无法计算距离
        return ((self.latitude - latitude) ** 2 + (self.longitude - longitude) ** 2) ** 0.5

class Diary(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    image = models.ImageField(upload_to='diary_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.IntegerField(default=0)
    popularity = models.IntegerField(default=0)
    can_modify_rating = models.BooleanField(default=True)
    likes = models.ManyToManyField(User, related_name='liked_diaries', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['attraction', 'rating']),
        ]

    def save(self, *args, **kwargs):
        # 压缩内容
        if self.content:
            try:
                # 将内容转换为字节
                content_bytes = self.content.encode('utf-8')
                # 使用zlib进行压缩
                compressed = zlib.compress(content_bytes)
                # 将压缩后的字节转换为base64字符串
                self.content = base64.b64encode(compressed).decode('utf-8')
            except Exception as e:
                logger.error(f"压缩内容时发生错误: {str(e)}")
        super().save(*args, **kwargs)

    def get_content(self):
        # 解压内容
        if self.content:
            try:
                # 将base64字符串转换回字节
                compressed_bytes = base64.b64decode(self.content)
                # 使用zlib解压
                decompressed = zlib.decompress(compressed_bytes)
                # 将解压后的字节转换回字符串
                return decompressed.decode('utf-8')
            except Exception as e:
                logger.error(f"解压内容时发生错误: {str(e)}")
                return self.content
        return ''

    def update_popularity(self):
        self.popularity = self.likes.count() * 0.4 + self.views * 0.3 + self.diary_comments.count() * 0.3
        self.save()

    def increment_views(self):
        self.views += 1
        self.update_popularity()
        self.save()

    def __str__(self):
        return self.title

class DiaryComment(models.Model):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='diary_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '日记评论'
        verbose_name_plural = verbose_name

class DiaryLike(models.Model):
    diary = models.ForeignKey(Diary, on_delete=models.CASCADE, related_name='diary_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('diary', 'user')

class FoodReview(models.Model):
    """美食评价模型"""
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='reviews', verbose_name='美食')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)], verbose_name='评分')
    content = models.TextField(blank=True, verbose_name='评价内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        unique_together = ('food', 'user')
        verbose_name = '美食评价'
        verbose_name_plural = '美食评价'
    
    def __str__(self):
        return f"{self.user.username}对{self.food.name}的评价"