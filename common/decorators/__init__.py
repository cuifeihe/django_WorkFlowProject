import os.path
from Log.log_config import LogConfig
from functools import wraps
from interface.api_response import response
import traceback
from django.conf import settings
from app_account.models import User

def check_admin_permission(user: User):
    """
    检查用户是否具有admin权限
    :param user:
    :param permission:
    :return:
    """
    if user.user_type == 'super_admin':
        return True
    else:
        return False


def check_workflow_admin_permission(user: User):
    """
    检查是否具有workflow_admin权限
    :param user:
    :return:
    """
    if user.user_type == 'workflow_admin' or user.user_type == 'super_admin':
        return True
    else:
        return False


def permission_check(permission=None):
    """
    检查权限的装饰器
    :param permission:
    :return:
    """

    def outer(func):
        @wraps(func)
        def deco(view, request, *args, **kwargs):

            if permission == 'super_admin':
                flag = check_admin_permission(request.user)
                if flag is False:
                    return response(400, '没有超级管理员权限', {})

            elif permission == 'workflow_admin':
                flag = check_workflow_admin_permission(request.user)
                if flag is False:
                    return response(400, '没有超级管理员或工作流管理员权限', {})

            result = func(view, request, *args, **kwargs)
            return result

        return deco

    return outer


def log_auto(func):
    """
    记录日志的装饰器
    :func: 实例方法或类方法
    :return:
    """

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except Exception as e:
            base_path = str(settings.BASE_DIR) + '/Log/'
            # base_path = 'E:/learning/programmer_learning/PycharmProjects/django_study/WorkflowProject/Log/'
            class_name = func.__qualname__.split('.')[0]
            path = f'{base_path}' + f'{class_name}'
            if not os.path.exists(path):
                os.mkdir(path)
            logfile = f'{path}' + f'/{func.__name__}.log'
            LogConfig(func.__name__, logfile, traceback.format_exc())
            # return False, e.__str__()
            # return False, '提交参数错误'
            raise ValueError('请求参数错误')
    return inner
