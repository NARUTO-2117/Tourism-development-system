# Generated by Django 5.2 on 2025-05-30 11:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TourismSystem', '0006_attraction_description'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='diary',
            options={'ordering': ['-created_at'], 'verbose_name': '旅游日记', 'verbose_name_plural': '旅游日记'},
        ),
        migrations.RemoveField(
            model_name='diary',
            name='can_modify_rating',
        ),
        migrations.RemoveField(
            model_name='diary',
            name='diary_id',
        ),
        migrations.RemoveField(
            model_name='diary',
            name='rating_count',
        ),
        migrations.RemoveField(
            model_name='diary',
            name='tags',
        ),
        migrations.AddField(
            model_name='diary',
            name='likes',
            field=models.ManyToManyField(blank=True, related_name='liked_diaries', to=settings.AUTH_USER_MODEL, verbose_name='点赞'),
        ),
        migrations.AddField(
            model_name='diary',
            name='views',
            field=models.IntegerField(default=0, verbose_name='浏览量'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='attraction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='TourismSystem.attraction', verbose_name='景点'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='作者'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='content',
            field=models.TextField(verbose_name='内容'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='diaries/', verbose_name='图片'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='popularity',
            field=models.FloatField(default=0, verbose_name='热度'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='rating',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=3, verbose_name='评分'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='title',
            field=models.CharField(max_length=200, verbose_name='标题'),
        ),
        migrations.AlterField(
            model_name='diary',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='diarylike',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diary_likes', to='TourismSystem.diary'),
        ),
        migrations.AddIndex(
            model_name='diary',
            index=models.Index(fields=['title'], name='TourismSyst_title_453cdb_idx'),
        ),
        migrations.AddIndex(
            model_name='diary',
            index=models.Index(fields=['created_at'], name='TourismSyst_created_ddf356_idx'),
        ),
        migrations.AddIndex(
            model_name='diary',
            index=models.Index(fields=['popularity'], name='TourismSyst_popular_d688e1_idx'),
        ),
        migrations.AddIndex(
            model_name='diary',
            index=models.Index(fields=['rating'], name='TourismSyst_rating_97002b_idx'),
        ),
    ]
