# from django.shortcuts import render
#
# # Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User

from .forms import RegisterForm, ProfileForm, ResetPasswordByPhoneForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user, profile = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # 保持会话
            messages.success(request, "密码已更新")
            return redirect("accounts:profile")
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, "accounts/change_password.html", {"form": form})


def reset_password_by_phone(request):
    """
    通过用户名 + 预留手机号重置密码，适用于忘记密码无法登录的用户。
    """
    if request.method == "POST":
        form = ResetPasswordByPhoneForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            phone = form.cleaned_data["phone"]
            new_pwd = form.cleaned_data["new_password"]

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                form.add_error("username", "用户不存在")
            else:
                profile = getattr(user, "profile", None)
                if not profile:
                    form.add_error("username", "该账号未绑定乘客资料，无法通过手机号重置")
                elif profile.phone != phone:
                    form.add_error("phone", "手机号与账号不匹配")
                else:
                    user.set_password(new_pwd)
                    user.save()
                    messages.success(request, "密码已重置，请使用新密码登录")
                    return redirect("accounts:login")
    else:
        form = ResetPasswordByPhoneForm()

    return render(request, "accounts/reset_password.html", {"form": form})
