import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from common.account import account_ins
from django.views import View
from django.utils.decorators import method_decorator
from common.decorators import permission_check
from interface.api_response import response
from django.views.decorators.csrf import ensure_csrf_cookie

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginView(View):
    """用户登录"""
    def get(self, request, *args, **kwargs):
        return response(code=200, msg='login页面', data=0)


    def post(self, request: HttpRequest, *args, **kwargs):
        dict_data = request.data # 中间件赋予data属性
        result = account_ins.user_login(request, **dict_data)
        if result:
            print(f'工号{result.get("job_id")}登录成功')
            code, msg, data = 200, '登录成功', result# 登录成功也可以跳转至某页
            return response(code, msg, data)
        return response(400, '找不到用户，用户名或密码错误', {})


@method_decorator(login_required, name='dispatch')
class IndexView(View):
    """个人主页"""
    def get(self, request, *args, **kwargs):
        """返回用户基本信息"""
        job_id = kwargs.get('job_id')
        if request.user.job_id == str(job_id):
            user_detail = request.user.user_info
            return response(200, '返回的用户信息', user_detail)
        return response(400, 'url不合法', {})


@method_decorator(login_required, name='dispatch')
class SetPwd(View):
    """普通用户登录后修改密码"""
    def get(self, request, *args, **kwargs):
        return response(200, '修改密码页面', {})

    def post(self, request, *args, **kwargs):
        """修改密码"""
        dict_data = request.data
        flag, result = account_ins.set_pwd(request, **dict_data)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '密码修改成功', result
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class RegisterView(View): # 测试用，超级管理员hehe  001  hehe1234
    """注册用户，需要工作流管理员或超级管理员登录后增加普通用户"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        return response(code=200, msg='注册页面', data=0)
        pass

    @permission_check(permission='workflow_admin')
    def post(self, request, *args, **kwargs):
        """超级管理员、工作流管理员可以创建普通用户"""
        dict_data = request.data
        # dict_data['creator'] = request.user.id
        flag, result = account_ins.add_user(**dict_data)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '已创建用户', result
        return response(code, msg, data)

@method_decorator(login_required, name='dispatch')
class AppointWorkflowAdmin(View):
    """超级管理员任命普通用户为工作流管理员"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """检索出目标用户信息"""
        job_id_list = request.GET.lists()
        flag, result = account_ins.get_user_info_by_job_id(job_id_list=job_id_list)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '用户已返回', result
        return response(code, msg, data)

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """指定某些用户为工作流管理员"""
        data = request.data
        flag, result = account_ins.set_user_workflow_admin_by_job_id(**data)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '用户已设置为工作流管理员', result
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class AppointCommon(View):
    """超级管理员将工作流管理员改为普通用户"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """检索出目标用户信息"""
        job_id_list = request.GET.lists()
        flag, result = account_ins.get_user_info_by_job_id(job_id_list=job_id_list)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '用户已返回', result
        return response(code, msg, data)

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """指定某些工作流管理员为普通用户"""
        data = request.data
        flag, result = account_ins.set_common_by_job_id(**data)
        if flag is False:
            code, msg, data = 400, result, {}
        else:
            code, msg, data = 200, '工作流管理员已修改为普通用户', result
        return response(code, msg, data)



@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    """账户注销"""
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/app_account/login')


@method_decorator(login_required, name='dispatch')
class DepartView(View):
    """部门设置，super_admin可以查看所有部门，增加部门"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """分页返回所有部门信息"""
        data = request.GET.dict()
        flag, result = account_ins.get_depart(**data)
        if flag is True:
            code, msg, data = 200, '部门信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

@method_decorator(login_required(), name='dispatch')
class AddDepartView(View):
    """super_admin增加部门信息"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '增加部门信息页面', {})

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """增加部门"""
        dict_data = request.data
        dict_data['creator'] = request.user.id
        flag, result = account_ins.add_depart(**dict_data)
        if flag is True:
            code, msg, data = 200, '部门已添加', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class DepartEditView(View):
    """修改、删除某部门，url中指定depart_id"""
    @permission_check('super_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '更新、删除部门信息页面', {})

    @permission_check('super_admin')
    def patch(self, request, *args, **kwargs):
        """更新部门信息"""
        depart_id = kwargs.get('depart_id')
        dict_data = request.data
        dict_data['depart_id'] = depart_id
        dict_data['creator'] = request.user.id
        flag, result = account_ins.update_depart(**dict_data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

    @permission_check('super_admin')
    def delete(self, request, *args, **kwargs):
        """删除部门信息"""
        depart_id = kwargs.get('depart_id')
        # dict_data = request.data
        flag, result = account_ins.delete_depart(depart_id)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


class DepartRelateUserView(View):
    """部门-用户关系；部门里 查看用户"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """分页返回部门内所有用户的信息"""
        depart_id = kwargs.get('depart_id')
        data = request.GET.dict()
        data['depart_id'] = depart_id
        flag, result = account_ins.get_depart_relate_user(**data)
        if flag is True:
            code, msg, data = 200, '部门内的用户信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


class DepartRelateUserEditView(View):
    """部门-用户关系；部门里 添加、修改、删除用户"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """返回编辑界面"""
        return response(200, '部门-用户 编辑界面', {})

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """部门里添加用户"""
        depart_id = kwargs.get('depart_id')
        data = request.data
        data['creator'] = request.user.id
        data['depart_id'] = depart_id
        flag, result = account_ins.add_depart_relate_user(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

    @permission_check('super_admin')
    def patch(self, request, *args, **kwargs):
        """修改部门里的用户，用户在部门之间转移"""
        depart_id = kwargs.get('depart_id')
        data = request.data
        data['depart_id'] = depart_id
        flag, result = account_ins.change_relation_of_user_and_depart(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


    @permission_check('super_admin')
    def delete(self, request, *args, **kwargs):
        """删除部门里的用户"""
        depart_id = kwargs.get('depart_id')
        data = request.data
        data['depart_id'] = depart_id
        flag, result = account_ins.delete_user_from_depart(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class JobView(View):
    """岗位设置， super_admin可以查看所有岗位"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """分页返回所有岗位信息"""
        data = request.GET.dict()
        flag, result = account_ins.get_jobtitle(**data)
        if flag is True:
            code, msg, data = 200, '岗位信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

@method_decorator(login_required, name='dispatch')
class AddJobView(View):
    """super_admin增加岗位"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '增加岗位信息页面', {})

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """增加岗位"""
        dict_data = request.data
        dict_data['creator'] = request.user.id
        flag, result = account_ins.add_job(**dict_data)
        if flag is True:
            code, msg, data = 200, '岗位已添加', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class JobEditView(View):
    """修改、删除某岗位，url中指定jobtitle_id"""
    @permission_check('super_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '更新、删除岗位信息页面', {})

    @permission_check('super_admin')
    def patch(self, request, *args, **kwargs):
        """更新岗位信息"""
        dict_data = request.data
        dict_data['jobtitle_id'] = kwargs.get('jobtitle_id')
        dict_data['creator'] = request.user.id
        flag, result = account_ins.update_job(**dict_data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


    @permission_check('super_admin')
    def delete(self, request, *args, **kwargs):
        """删除岗位"""
        jobtitle_id = kwargs.get('jobtitle_id')
        # dict_data = request.data
        flag, result = account_ins.delete_job(jobtitle_id)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class JobRelateUserView(View):
    """在岗位里：查看用户"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """获取指定岗位的用户信息"""
        jobtitle_id = kwargs.get('jobtitle_id')
        data = request.GET.dict()
        data['jobtitle_id'] = jobtitle_id
        flag, result = account_ins.get_job_relate_user(**data)
        if flag is True:
            code, msg, data = 200, '岗位内的用户信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

@method_decorator(login_required, name='dispatch')
class JobRelateUserEditView(View):
    """在岗位里：添加、修改、删除用户"""
    @permission_check(permission='super_admin')
    def get(self, request, *args, **kwargs):
        """返回编辑界面"""
        return response(200, '岗位-用户 编辑界面', {})

    @permission_check(permission='super_admin')
    def post(self, request, *args, **kwargs):
        """
        指定岗位里添加用户
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        jobtitle_id = kwargs.get('jobtitle_id')
        data = request.data
        data['creator'] = request.user.id
        data['jobtitle_id'] = jobtitle_id
        flag, result = account_ins.add_job_relate_user(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

    @permission_check('super_admin')
    def patch(self, request, *args, **kwargs):
        """修改岗位里的用户，用户在岗位之间转移"""
        jobtitle_id = kwargs.get('jobtitle_id')
        data = request.data
        data['jobtitle_id'] = jobtitle_id
        flag, result = account_ins.change_relation_of_user_and_job(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

    @permission_check('super_admin')
    def delete(self, request, *args, **kwargs):
        """删除岗位里的用户"""
        jobtitle_id = kwargs.get('jobtitle_id')
        data = request.data
        data['jobtitle_id'] = jobtitle_id
        flag, result = account_ins.delete_user_from_job(**data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


