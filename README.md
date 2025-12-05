1.下载好代码后确认自己的python版本和postgreSQL版本，选择一个兼容的Django版本pip
2.然后在air_ticket_system/settings.py里面修改如下信息，确保和你的本地创建的数据库一样
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "airticket_db",//修改成你的创建的数据库的名字
        "USER": "postgres",//你的postgreSQL的的管理员账号
        "PASSWORD": "你的密码",//你的postgreSQL的管理员密码
        "HOST": "localhost",//端口设置，别冲突就行
        "PORT": "5432",
    }
}
3.在虚拟环境中执行python manage.py migrate
4.可以执行python manage.py createsuperuser来创建管理员账户
5.python manage.py runserver用于启动

