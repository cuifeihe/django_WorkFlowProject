
from django.urls import path, include
from .views import LoginView, RegisterView, \
    LogoutView, DepartView, JobView, SetPwd, DepartEditView, JobEditView, \
    JobRelateUserView, DepartRelateUserView, AppointWorkflowAdmin, IndexView, AppointCommon, AddDepartView, \
    DepartRelateUserEditView, AddJobView, JobRelateUserEditView

from django.views import View


urlpatterns = [
    path('index/<str:job_id>', IndexView.as_view()), # 个人主页
    path('login/', LoginView.as_view()), # 用户初始登录
    path('login/set_pwd/', SetPwd.as_view()), # 注册后的用户登录后修改密码
    path('logout/', LogoutView.as_view()), # 注销
    path('register/', RegisterView.as_view()), # 管理员进行用户注册

    path('appoint_workflow_admin/', AppointWorkflowAdmin.as_view()), # 管理员指定一个或多个用户（GET请求，查询字符串?job_id=1&job_id=2获得用户，POST请求发送job_id列表设置用户）为工作流管理员
    path('appoint_common/', AppointCommon.as_view()), # 管理员指定一个或多个工作流管理员（GET请求，查询字符串?job_id=1&job_id=2获得用户，POST请求发送job_id列表设置用户）为普通用户


    path('depart/', DepartView.as_view()), # 管理员使用，查看(分页、url查询字符串)部门信息
    path('add_depart/', AddDepartView.as_view()), # 管理员使用，添加部门
    path('depart/edit/<int:depart_id>', DepartEditView.as_view()), # 管理员使用，修改、删除指定部门

    path('depart/view/depart<int:depart_id>/relate_user/', DepartRelateUserView.as_view()), # 管理员使用，查看部门成员
    path('depart/edit/depart<int:depart_id>/relate_user/', DepartRelateUserEditView.as_view()), # 管理员用户， 添加、更新、删除部门成员


    path('job/', JobView.as_view()), # 管理员使用，查看(分页、url查询字符串)岗位
    path('add_job/', AddJobView.as_view()), # 管理员使用，添加岗位
    path('job/edit/<int:jobtitle_id>', JobEditView.as_view()), # 管理员使用，修改、删除指定岗位

    path('job/view/job<int:jobtitle_id>/relate_user/', JobRelateUserView.as_view()), # 管理员使用，查看岗位成员
    path('job/edit/job<int:jobtitle_id>/relate_user/', JobRelateUserEditView.as_view()), # 管理员使用，添加、更新、删除岗位成员


]