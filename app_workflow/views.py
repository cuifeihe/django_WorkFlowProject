from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render
# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from common.decorators import permission_check
from common.workflow import workflow_ins
from interface.api_response import response

@method_decorator(login_required, name='dispatch')
class WorkflowIndexView(View):
    """获取所有工作流"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        """根据用户身份返回工作流"""
        data = request.GET.dict()
        data['user_id'] = request.user.id
        data['user_type'] = request.user.user_type
        flag, result = workflow_ins.get_all_workflow_info(**data)
        if flag is True:
            code, msg, data = 200, '工作流信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class AddWorkflowView(View):
    """新增工作流模板"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '新增工作流页面', {})

    @permission_check(permission='workflow_admin')
    def post(self, request, *args, **kwargs):
        dict_data = request.data
        dict_data['creator'] = request.user.id
        flag, result = workflow_ins.add_workflow(**dict_data)
        if flag is True:
            code, msg, data = 200, '工作流已添加', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class GetWorkflowDetailView(View):
    """获取工作流详细信息（所有用户均可）"""
    def get(self, request: HttpRequest, *args, **kwargs):
        workflow_id = kwargs.get('workflow_id')
        flag, result = workflow_ins.get_workflow_detail(workflow_id)
        if flag is True:
            code, msg, data = 200, '工作流详细信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class WorkflowEditView(View):
    """配置工作流具体流程"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '编辑工作流界面', {})

    @permission_check(permission='workflow_admin')
    def post(self, request, *args, **kwargs):
        """配置工作流流程"""
        workflow_id = kwargs.get('workflow_id')
        dict_data = request.data
        dict_data['creator'] = request.user.id
        dict_data['workflow_id'] = workflow_id
        flag, result = workflow_ins.add_workflow_detail(**dict_data)
        if flag is True:
            code, msg, data = 200, '工作流内容已添加', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class WorkflowDeleteView(View):
    """删除某工作流"""
    @permission_check(permission='workflow_admin')
    def delete(self, request, *args, **kwargs):
        """删除工作流"""
        workflow_id = kwargs.get('workflow_id')
        user_obj = request.user
        flag, result = workflow_ins.delete_workflow(workflow_id, user_obj)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class WorkflowFunctionSwitchView(View):
    """配置某工作流的功能开关"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        return response(200, '配置工作流功能开关的界面', {})

    @permission_check(permission='workflow_admin')
    def post(self, request, *args, **kwargs):
        data = request.data
        data['workflow_id'] = kwargs.get('workflow_id')
        flag, result = workflow_ins.set_workflow_function_switch(request.user, **data)
        if flag is True:
            code, msg, data = 200, result, {}
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)




