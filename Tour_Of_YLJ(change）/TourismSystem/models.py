from django.db import models

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