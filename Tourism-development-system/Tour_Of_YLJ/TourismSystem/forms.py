from django import forms
from .models import Diary
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinLengthValidator, RegexValidator

class DiaryForm(forms.ModelForm):
    class Meta:
        model = Diary
        fields = ['title', 'content', 'image', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'rating': forms.HiddenInput(),  # 使用隐藏字段，因为我们在模板中使用自定义的星级评分
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'title': {
                'required': '请输入标题',
                'max_length': '标题不能超过200个字符',
            },
            'content': {
                'required': '请输入内容',
            },
            'rating': {
                'required': '请选择评分',
                'min_value': '评分不能小于1',
                'max_value': '评分不能大于5',
            },
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('图片大小不能超过5MB')
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError('只能上传图片文件')
        return image

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None:
            raise forms.ValidationError('请选择评分')
        try:
            rating = float(rating)
            if rating < 1 or rating > 5:
                raise forms.ValidationError('评分必须在1到5之间')
            return rating
        except (TypeError, ValueError):
            raise forms.ValidationError('评分必须是1到5之间的数字')

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        required=True,
        validators=[
            MinLengthValidator(3, message='用户名至少需要3个字符'),
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='用户名只能包含字母、数字和下划线'
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'})
    )
    password1 = forms.CharField(
        required=True,
        validators=[MinLengthValidator(8, message='密码至少需要8个字符')],
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请确认密码'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已被使用')
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('两次输入的密码不一致')
        return password2