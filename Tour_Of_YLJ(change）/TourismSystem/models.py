from django.db import models
from django.contrib.auth.models import User
import zlib
import json

class spots_1(models.Model):
    name = models.CharField(max_length=100)          # 名称
    category = models.CharField(max_length=50)       # 分类
    epithet = models.CharField(max_length=200)       # 称号/绰号
    popularity = models.IntegerField(default=0)      # 人气值（默认0）
    rating = models.FloatField(default=0.0)         # 评分（默认0.0）
    def __str__(self):
        return self.name

class spots_2(models.Model):
    spots_1 = models.ForeignKey(spots_1, on_delete=models.CASCADE)  # 关键：关联到spots_1
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    epithet = models.CharField(max_length=200)
    popularity = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    def __str__(self):
        return self.name

class spots_3(models.Model):
    spots_1 = models.ForeignKey(spots_2, on_delete=models.CASCADE)  # 关键：关联到spots_2
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    epithet = models.CharField(max_length=200)
    popularity = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    def __str__(self):
        return self.name

class TravelDiary(models.Model):
    title = models.CharField(max_length=200)  # 日记标题
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # 作者
    content = models.TextField()  # 原始内容
    compressed_content = models.BinaryField(null=True)  # 压缩后的内容
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    updated_at = models.DateTimeField(auto_now=True)  # 更新时间
    views = models.IntegerField(default=0)  # 浏览量
    rating = models.FloatField(default=0.0)  # 评分
    total_ratings = models.IntegerField(default=0)  # 评分人数
    location = models.ForeignKey(spots_1, on_delete=models.SET_NULL, null=True)  # 关联的景点

    def save(self, *args, **kwargs):
        # 压缩内容
        if self.content:
            compressed = zlib.compress(self.content.encode('utf-8'))
            self.compressed_content = compressed
        super().save(*args, **kwargs)

    def get_decompressed_content(self):
        # 解压内容
        if self.compressed_content:
            return zlib.decompress(self.compressed_content).decode('utf-8')
        return self.content

    def add_rating(self, new_rating):
        # 添加新评分
        self.rating = (self.rating * self.total_ratings + new_rating) / (self.total_ratings + 1)
        self.total_ratings += 1
        self.save()

    def __str__(self):
        return self.title

class DiaryRating(models.Model):
    diary = models.ForeignKey(TravelDiary, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.FloatField()
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('diary', 'user')  # 确保每个用户只能对同一篇日记评分一次