from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View

from common.decorators import permission_check
from common.ticket import ticket_ins
from interface.api_response import response

@method_decorator(login_required, name='dispatch')
class TicketGetView(View):
    """用户获得工单信息（我提交的、我审批的）"""
    def get(self, request, *args, **kwargs):
        get_type = request.GET.get('type', 'my_submit')
        per_page = request.GET.get('per_page', 10)
        page = request.GET.get('page', 1)
        flag, res = ticket_ins.user_get_ticket(get_type, request.user, per_page, page)
        if flag is True:
            code, msg, data = 200, '用户工单信息已返回', res
        else:
            code, msg, data = 400, res, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class AddCountersignView(View):
    """临时加签"""
    def get(self, request, *args, **kwargs):
        return response(200, '返回加签页面', {})

    def post(self, request, *args, **kwargs):
        data = request.data
        data['ticket_id'] = kwargs.get('ticket_id')
        flag, result = ticket_ins.add_countersign(request.user, **data)
        if flag is True:
            code, msg, data = 200, '加签设置成功', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class TicketListView(View):
    """工作流管理员分页获得所有工单的列表（可根据提交人、工单title 搜索）"""
    @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        data = request.GET.dict()
        flag, result = ticket_ins.get_ticket(**data)
        if flag is True:
            code, msg, data = 200, '工单信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class TicketApproveGetView(View):
    """用户登录，获得自己的待审批工单、进行审批"""
    # @permission_check(permission='workflow_admin')
    def get(self, request, *args, **kwargs):
        """获取待自己审批的工单"""
        # approver_id = request.user.id
        user_obj = request.user
        flag, result = ticket_ins.need_approve_ticket(user_obj)
        if flag is True:
            code, msg, data = 200, '待审批工单信息已返回', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class WithdrawTicketView(View):
    """工单提交人中途撤销工单"""
    def get(self, request, *args, **kwargs):
        ticket_id = kwargs.get('ticket_id')
        flag, result = ticket_ins.withdraw_ticket(request.user, ticket_id)
        if flag is True:
            code, msg, data = 200, '您发起的审批工单已撤销', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class TransferTicketView(View):
    """转交工单给其他人审批"""
    def get(self, request, *args, **kwargs):
        return response(200, '返回转交页面', {})

    def post(self, request, *args, **kwargs):
        dict_data = request.data
        dict_data['ticket_id'] = kwargs.get('ticket_id')
        flag, result = ticket_ins.transfer_ticket(request.user, **dict_data)
        if flag is True:
            code, msg, data = 200, '已临时转移给其他人审批', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)


@method_decorator(login_required, name='dispatch')
class TicketApproveView(View):
    """对某工单进行审批"""
    def get(self, request, *args, **kwargs):
        return response(200, '返回审批页面', {})

    def post(self, request, *args, **kwargs):
        """提交审批"""
        dict_data = request.data
        # dict_data['user_id'] = request.user.id
        dict_data['ticket_id'] = kwargs.get('ticket_id')
        flag, result = ticket_ins.approve_ticket(request.user, **dict_data)
        if flag is True:
            code, msg, data = 200, '审批完成', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

@method_decorator(login_required, name='dispatch')
class TicketSubmitView(View):
    """提交工单"""

    def get(self, request, *args, **kwargs):
        return response(200, '提交工单页面', {})

    def post(self, request, *args, **kwargs):
        dict_data = request.data
        dict_data['creator'] = request.user.id
        flag, result = ticket_ins.submit_ticket(request.user, **dict_data)
        if flag is True:
            code, msg, data = 200, '工单已提交', result
        else:
            code, msg, data = 400, result, {}
        return response(code, msg, data)

