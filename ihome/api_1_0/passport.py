# coding:utf-8

import re
from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db, constants
from ihome.models import User


# POST /api/v1_0/users
@api.route("/users", methods=["POST"])
def register():
    """用户注册"""
    # 接受参数, 手机号、短信验证码、密码, json格式的数据
    # json.loads(request.data)
    # request.get_json方法能够帮助将请求体的json数据转换为字典
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")

    # 校验参数
    if not all([mobile, sms_code, password]):
        resp = {
            "errno": RET.PARAMERR,
            "errmsg": "参数不完整"
        }
        return jsonify(resp)

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "手机号格式错误"
        }
        return jsonify(resp)

    # 业务逻辑
    # 获取真实的短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "查询短信验证码错误"
        }
        return jsonify(resp)

    # 判断短信验证码是否过期
    if real_sms_code is None:
        resp = {
            "errno": RET.NODATA,
            "errmsg": "短信验证码过期"
        }
        return jsonify(resp)

    # 对于用户输入的短信验证码是否正确
    if real_sms_code != sms_code:
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "短信验证码错误"
        }
        return jsonify(resp)

    # 删除短信验证码
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断手机号是否注册
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     resp = {
    #         "errno": RET.DBERR,
    #         "errmsg": "数据库异常"
    #     }
    #     return jsonify(resp)
    #
    # if user is not None:
    #     # 表示已经注册过
    #     resp = {
    #         "errno": RET.DATAEXIST,
    #         "errmsg": "用户手机号已经注册"
    #     }
    #     return jsonify(resp)

    # 保存用户的数据到数据库中

    user = User(name=mobile, mobile=mobile)
    # 对于password属性的设置，会调用属性方法，进行加密操作
    user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        # 表示已经注册过
        resp = {
            "errno": RET.DATAEXIST,
            "errmsg": "用户手机号已经注册"
        }
        return jsonify(resp)

    # 利用session记录用户的登录状态

    session["user_id"] = user.id
    session["user_name"] = mobile
    session["mobile"] = mobile

    # 返回值
    resp = {
        "errno": RET.OK,
        "errmsg": "注册成功"
    }
    return jsonify(resp)


@api.route("/sessions", methods=["POST"])
def login():
    """登录"""
    # 获取参数、用户手机号  密码
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 检验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

    # 判断用户的错误次数
    # 从redis中获取错误次数
    user_ip = request.remote_addr
    try:
        access_counts = redis_store.get("access_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        # 如果有错误次数记录，并且超过最大次数，直接返回
        if access_counts is not None and int(access_counts) >= constants.LOGIN_ERROR_MAX_NUM:
            return jsonify(errno=RET.REQERR, errmsg="登录过于频繁")

    # 查询数据库，判断用户信息与密码
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询用户信息异常")

    if user is None or not user.check_password(password):
        # 出现错误，累加错误次数
        try:
            redis_store.incr("access_%s" % user_ip)
            redis_store.expire("access_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.LOGINERR, errmsg="用户名或密码失败")

    # 登录成功，
    # 清除用户的登录错误次数
    try:
        redis_store.delete("access_%s" % user_ip)
    except Exception as e:
        current_app.logger.error(e)

    # 保存用户的登录状态
    session["user_id"] = user.id
    session["user_name"] = user.name
    session["mobile"] = user.mobile

    return jsonify(errno=RET.OK, errmsg="用户登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get("user_name")
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    """登出"""
    # 清除session数据
    # session.clear()
    #建议用下面这种方法清楚session数据
    session.pop("user_id")
    session.pop("user_name")
    session.pop("mpbile")
    return jsonify(errno=RET.OK, errmsg="OK")





