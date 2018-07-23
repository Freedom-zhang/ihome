# coding:utf-8

from flask import Blueprint, current_app, make_response
from flask_wtf.csrf import generate_csrf


html = Blueprint("html", __name__)

# 提供静态的html文件
# 127.0.0.1:5000/
# 127.0.0.1:5000/index.html
# 127.0.0.1:5000/register.html
# 127.0.0.1:5000/favicon.ico  # 浏览器自动访问这个路径，获取网站的logo标志


@html.route("/<re(r'.*'):file_name>")
def get_html_file(file_name):
    """提供html文件"""
    # 根据用户访问的路径指明的html文件名file_name，提供相对应的html文件
    if not file_name:
        # 表示用户访问的是 /
        file_name = "index.html"

    if file_name != "favicon.ico":
        file_name = "html/" + file_name

    # 使用wtf帮助我们生成csrf_token字符串
    csrf_token = generate_csrf()

    # 为用户设置cookie  csrf_token
    resp = make_response(current_app.send_static_file(file_name))
    resp.set_cookie("csrf_token", csrf_token)

    return resp
