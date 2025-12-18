from django import forms
from django.contrib.auth.models import User
from .models import PassengerProfile
from django.contrib.auth.forms import PasswordChangeForm


class RegisterForm(forms.ModelForm):
    username = forms.CharField(label="用户名", max_length=150)
    password = forms.CharField(
        label="密码", widget=forms.PasswordInput()
    )
    password_confirm = forms.CharField(
        label="确认密码", widget=forms.PasswordInput()
    )

    class Meta:
        model = PassengerProfile
        fields = ["real_name", "id_card_no", "phone", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("用户名已存在")
        return username

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        pwd2 = cleaned.get("password_confirm")
        if pwd and pwd2 and pwd != pwd2:
            self.add_error("password_confirm", "两次密码不一致")
        return cleaned

    def save(self, commit=True):
        cleaned = self.cleaned_data
        user = User.objects.create_user(
            username=cleaned["username"],
            password=cleaned["password"],
            email=cleaned["email"],
        )
        profile = PassengerProfile.objects.create(
            user=user,
            real_name=cleaned["real_name"],
            id_card_no=cleaned["id_card_no"],
            phone=cleaned["phone"],
            email=cleaned["email"],
        )
        return user, profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = PassengerProfile
        fields = ["real_name", "id_card_no", "phone", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")


class ResetPasswordByPhoneForm(forms.Form):
    username = forms.CharField(label="用户名", max_length=150)
    phone = forms.CharField(label="预留手机号", max_length=20)
    new_password = forms.CharField(label="新密码", widget=forms.PasswordInput())
    confirm_password = forms.CharField(label="确认新密码", widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", "form-control")

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get("new_password")
        pwd2 = cleaned.get("confirm_password")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error("confirm_password", "两次输入的密码不一致")
        return cleaned
