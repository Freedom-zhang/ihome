# coding:utf-8

from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from ihome.utils.response_code import RET
from functools import wraps


class RegexConverter(BaseConverter):
    """自定义的接受正则表达式的路由转换器"""
    def __init__(self, url_map, regex):
        """regex是在路由中填写的正则表达式"""
        super(RegexConverter, self).__init__(url_map)
        self.regex = regex

#自定义装饰器
def login_required(view_func):
    """检验用户的登录状态"""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is not None:
            # 表示用户已经登录
            # 使用g对象保存user_id，在视图函数中可以直接使用
            g.user_id = user_id
            return view_func(*args, **kwargs)
        else:
            # 用户未登录
            resp = {
                "errno": RET.SESSIONERR,
                "errmsg": "用户未登录"
            }
            return jsonify(resp)
    return wrapper