from django.contrib import admin
from .models import Attraction, Diary, DiaryComment, DiaryLike

admin.site.register(Attraction)
admin.site.register(Diary)
admin.site.register(DiaryComment)
admin.site.register(DiaryLike)