# coding:utf-8

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants, db
from flask import current_app, jsonify, make_response, request
from ihome.utils.response_code import RET
from ihome.libs.yuntongxun.sms import CCP
import random
from ihome.models import User
from ihome.tasks import task_sms

# url: /api/v1_0/image_codes/<image_code_id>
#
# methods: get
#
# 传入参数：
#
# 返回值： 正常：图片  异常 json


@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """提供图片验证码"""
    # 业务处理
    # 生成验证码图片
    # 名字, 验证码真实值，图片的二进制内容
    name, text, image_data = captcha.generate_captcha()

    try:
        # 保存验证码的真实值与编号
        # redis_store.set("image_code_%s" % image_code_id, text)
        # redis_store.expires("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
        # 设置redis的数据与有效期
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 在日志中记录异常
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            # "errmsg": "save image code failed"
            "errmsg": "保存验证码失败"
        }
        return jsonify(resp)

    # 返回验证码图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1_0/sms_codes/<mobile>?image_code_id=xxx&image_code=xxxx
# 用户填写的图片验证码
# 图片验证码的编号
# 用户的手机号

# @api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
# def send_sms_code(mobile):
#     """发送短信验证码"""
#     # 获取参数
#     image_code_id = request.args.get("image_code_id")
#     image_code = request.args.get("image_code")
#
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         resp = {
#             "errno": RET.PARAMERR,
#             "errmsg": "参数不完整"
#         }
#         return jsonify(resp)
#
#     # 业务处理
#     # 取出真实的图片验证码
#     try:
#         real_image_code = redis_store.get("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno": RET.DBERR,
#             "errmsg": "获取图片验证码失败"
#         }
#         return jsonify(resp)
#
#     # 判断验证码的有效期
#     if real_image_code is None:
#         # 表示redis中没有这个数据
#         resp = {
#             "errno": RET.NODATA,
#             "errmsg": "图片验证码过期"
#         }
#         return jsonify(resp)
#
#     # 删除redis中的图片验证码，防止用户多次尝试同一个图片验证码
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 判断用户填写的验证码与真实的验证码
#     if real_image_code.lower() != image_code.lower():
#         # 表示用户填写错误
#         resp = {
#             "errno": RET.DATAERR,
#             "errmsg": "图片验证码有误"
#         }
#         return jsonify(resp)
#
#     # 判断用户手机号是否注册过
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 用户已经注册过
#             resp = {
#                 "errno": RET.DATAEXIST,
#                 "errmsg": "用户手机号已经注册过"
#             }
#             return jsonify(resp)
#
#     # 创建短信验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存短信验证码
#     try:
#         redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno": RET.DBERR,
#             "errmsg": "保存短信验证码异常"
#         }
#         return jsonify(resp)
#
#     # 发送验证码短信
#     try:
#         ccp = CCP()
#         result = ccp.send_template_sms(mobile, [sms_code, str(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         resp = {
#             "errno": RET.THIRDERR,
#             "errmsg": "发送短信异常"
#         }
#         return jsonify(resp)
#
#     if result == 0:
#         # 发送成功
#         resp = {
#             "errno": RET.OK,
#             "errmsg": "发送短信成功"
#         }
#         return jsonify(resp)
#     else:
#         resp = {
#             "errno": RET.THIRDERR,
#             "errmsg": "发送短信失败"
#         }
#         return jsonify(resp)



@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def send_sms_code(mobile):
    """发送短信验证码"""
    # 获取参数
    image_code_id = request.args.get("image_code_id")
    image_code = request.args.get("image_code")

    # 校验参数
    if not all([image_code_id, image_code]):
        resp = {
            "errno": RET.PARAMERR,
            "errmsg": "参数不完整"
        }
        return jsonify(resp)

    # 业务处理
    # 取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "获取图片验证码失败"
        }
        return jsonify(resp)

    # 判断验证码的有效期
    if real_image_code is None:
        # 表示redis中没有这个数据
        resp = {
            "errno": RET.NODATA,
            "errmsg": "图片验证码过期"
        }
        return jsonify(resp)

    # 删除redis中的图片验证码，防止用户多次尝试同一个图片验证码
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写的验证码与真实的验证码
    if real_image_code.lower() != image_code.lower():
        # 表示用户填写错误
        resp = {
            "errno": RET.DATAERR,
            "errmsg": "图片验证码有误"
        }
        return jsonify(resp)

    # 判断用户手机号是否注册过
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user is not None:
            # 用户已经注册过
            resp = {
                "errno": RET.DATAEXIST,
                "errmsg": "用户手机号已经注册过"
            }
            return jsonify(resp)

    # 创建短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        resp = {
            "errno": RET.DBERR,
            "errmsg": "保存短信验证码异常"
        }
        return jsonify(resp)

    # 使用celery发送验证码短信
    task_sms.send_template_sms.delay(mobile,[sms_code,str(constants.SMS_CODE_REDIS_EXPIRES/60)],1)

    return jsonify(errno=RET.OK,errmsg="OK")