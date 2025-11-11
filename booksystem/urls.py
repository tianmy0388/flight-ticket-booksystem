"""FlightTicket URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path

from . import views

app_name = 'booksystem'  # 添加这个属性，方便jinja语法

urlpatterns = [
    # 注册与登录
    re_path(r'^register/$', views.register, name='register'),  # 注册
    re_path(r'^login_user/$', views.login_user, name='login_user'),  # 登入
    re_path(r'^logout_user/$', views.logout_user, name='logout_user'),  # 登出
    # 主要页面
    re_path(r'^$', views.index, name='index'),  # 欢迎页面
    re_path(r'^result/$', views.result, name='result'),  # 搜索结果
    re_path(r'^user_info/$', views.user_info, name='user_info'),  # 用户信息
    re_path(r'^book/flight/(?P<flight_id>[0-9]+)/$', views.book_ticket, name='book_ticket'),  # 订票
    re_path(r'^refund/flight/(?P<flight_id>[0-9]+)/$', views.refund_ticket, name='refund_ticket'),  # 退票
]
