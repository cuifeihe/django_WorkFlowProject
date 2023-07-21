from django.contrib import admin
from django.urls import path, include
from .views import WorkflowIndexView, WorkflowEditView, AddWorkflowView, GetWorkflowDetailView, WorkflowDeleteView, \
    WorkflowFunctionSwitchView

urlpatterns = [
    # path('admin/', admin.site.urls),

    path('index/', WorkflowIndexView.as_view()), # 根据工作流名字搜索获取工作流、分页返回、（根据用户权限，工作流管理员获取自己的工作流；超级管理员获取所有工作流）
    path('workflow<int:workflow_id>/get_detail/', GetWorkflowDetailView.as_view()), # 获取某工作流具体信息
    path('add/', AddWorkflowView.as_view()),  # 工作流管理员新增工作流（初始信息）
    path('workflow<int:workflow_id>/edit/', WorkflowEditView.as_view()),  # 配置某工作流
    path('workflow<int:workflow_id>/delete/', WorkflowDeleteView.as_view()), #删除某工作流
    path('workflow<int:workflow_id>/function_switch/', WorkflowFunctionSwitchView.as_view()), # 配置已有工作流的功能开关（是否允许中途撤回审批、是否允许中途加签、是否允许中途移交他人审批、是否限制工单的提交申请及何种限制方式）

]