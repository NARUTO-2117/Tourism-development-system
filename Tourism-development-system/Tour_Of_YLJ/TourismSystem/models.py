from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import zlib
import base64
import logging

logger = logging.getLogger(__name__)

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
    description = models.TextField(blank=True, default='')  # 新增景点介绍字段

    class Meta:
        unique_together = ('name', 'parent')

    def __str__(self):
        return self.name

class Diary(models.Model):
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='作者')
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, verbose_name='景点')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, verbose_name='评分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    image = models.ImageField(upload_to='diary_images/', null=True, blank=True, verbose_name='图片')
    popularity = models.FloatField(default=0, verbose_name='热度')
    views = models.IntegerField(default=0, verbose_name='浏览量')
    can_modify_rating = models.BooleanField(default=True, verbose_name='可修改评分')
    likes = models.ManyToManyField(User, related_name='liked_diaries', blank=True, verbose_name='点赞')

    def __str__(self):
        return self.title

    def get_compressed_content(self):
        """获取压缩后的内容"""
        if not self.content:
            return ''
        try:
            # 将内容转换为字节
            content_bytes = self.content.encode('utf-8')
            # 使用zlib进行压缩
            compressed = zlib.compress(content_bytes)
            # 将压缩后的字节转换为base64字符串
            return base64.b64encode(compressed).decode('utf-8')
        except Exception as e:
            logger.error(f"压缩内容时发生错误: {str(e)}")
            return self.content

    def get_decompressed_content(self):
        """获取解压后的内容"""
        if not self.content:
            return ''
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

    def verify_compression(self):
        """验证压缩是否无损"""
        if not self.content:
            return True
        try:
            # 获取原始内容
            original_content = self.get_decompressed_content()
            # 重新压缩
            compressed = self.get_compressed_content()
            # 重新解压
            decompressed = self.get_decompressed_content()
            # 比较原始内容和重新解压后的内容
            return original_content == decompressed
        except Exception as e:
            logger.error(f"验证压缩时发生错误: {str(e)}")
            return False

    def save(self, *args, **kwargs):
        # 在保存前压缩内容
        if self.content:
            self.content = self.get_compressed_content()
            # 验证压缩是否无损
            if not self.verify_compression():
                logger.error("压缩验证失败：内容可能已损坏")
                raise ValueError("压缩验证失败：内容可能已损坏")
        super().save(*args, **kwargs)

    def update_popularity(self):
        """更新日记热度"""
        likes_count = self.likes.count()
        comments_count = self.diarycomment_set.count()
        self.popularity = likes_count * 0.4 + comments_count * 0.3 + self.views * 0.3
        self.save()
    
    def increment_views(self):
        """增加浏览量"""
        self.views += 1
        self.save()

    class Meta:
        ordering = ['-created_at']
        verbose_name = '旅游日记'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['created_at']),
            models.Index(fields=['popularity']),
            models.Index(fields=['rating']),
        ]

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