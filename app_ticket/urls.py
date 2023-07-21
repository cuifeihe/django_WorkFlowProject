
from django.urls import path, include
from .views import TicketListView, TicketApproveView, TicketApproveGetView, TicketSubmitView, TicketGetView, AddCountersignView, \
    WithdrawTicketView, TransferTicketView

urlpatterns = [
    path('submit_ticket/', TicketSubmitView.as_view()),   # 用户提交工单
    path('workflow_index/', TicketListView.as_view()), # 工作流管理员分页获得所有工单的列表（可根据提交人、工单title 搜索）index?search_value=''&apply_user_id=1&state='ongoing&per_page=10&page=1
    path('approve_ticket_get/', TicketApproveGetView.as_view()), # 用户登录，获得自己的待审批工单、进行审批
    path('approve/ticket<int:ticket_id>', TicketApproveView.as_view()), # 用户对某工单进行审批

    path('user_index/', TicketGetView.as_view()), # 用户分页获得工单（我提交的、我审批的），查询字符串user_index/?per_page=10&page=1&type=my_submit or my_approve
    path('add_countersign/ticket<int:ticket_id>', AddCountersignView.as_view()), # 中途加签功能（示例：当前工单审批人A可以发起临时加签，选择某人B成为临时审批人，待B审批通过后，继续回归原流程，由A继续审批）
    path('withdraw_ticket/ticket<int:ticket_id>', WithdrawTicketView.as_view()), # 中途撤销工单（工单发起人可以在中途撤销工单）
    path('transfer_ticket/ticket<int:ticket_id>', TransferTicketView.as_view()), # 中途移交他人审批（只有当前审批人能临时移交给他人审批）


]