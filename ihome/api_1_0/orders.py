# coding:utf-8

import datetime
from flask import request,g,jsonify,current_app
from ihome.utils.commons import login_required
from ihome import db,redis_store
from ihome.utils.response_code import RET
from ihome.models import House,Order
from . import api


@api.route("/orders",methods=["POST"])
@login_required
def save_order():
    """保存订单"""
    user_id = g.user_id

    #获取参数
    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    house_id = order_data.get("house_id") #预定的房屋编号
    start_date_str= order_data.get("start_date") #预定的起始时间
    end_date_str = order_data.get("end_date") #预定的结束时间

    #参数检查
    if not all([house_id,start_date_str,end_date_str]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")

    #日期格式检查
    try:
        #将请求的时间参数字符串转换为datatime类型
        start_date = datetime.datetime.strptime(start_date_str,"%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str,"%Y-%m-%d")
        assert start_date <= end_date

        #计算预定的天数
        days = (end_date - start_date).days + 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg="日期格式错误")

    #查询房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取房屋信息失败")
    if not house:
        return jsonify(errno=RET.DATAERR,errmsg="房屋不存在")

    #预定的房屋是否是房东自己的
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR,errmsg="不能预定自己的房屋")

    #确保用户预定时间内，房屋没有被别人下单
    try:
        # 查询时间冲突的订单数
        count = Order.query.filter(Order.house_id == house_id,Order.begin_date <= end_date,
                                   Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="检查出错，请稍后重试")
    if count >0:
        return jsonify(errno=RET.DATAERR,errmsg="房屋已被预定")

    #订单总额
    amount = days*house.price

    #保存数据
    order = Order()
    order.house_id = house_id
    order.user_id = user_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = amount

