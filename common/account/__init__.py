from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q

from app_account.models import User, Depart, JobTitle, UserDepart, UserJob
from interface.account_view_interface import AddUser, LoginData, SetPwd, \
    GetDepart, AddDepart, GetDepartRelateUser, AddDepartRelateUser, ChangeRelationOfDepartAndUser, DeleteUserFromDepart, \
    GetJobtitle, AddJob, GetJobRelateUser, AddJobRelateUser, ChangeRelationOfJobAndUser, DeleteUserFromJob, SetWorkflow, \
    SetCommon, UpdateDepart, UpdateJob
from interface.api_response import response
from common.decorators import log_auto

class AccountSupport(object):
    """账户管理相关方法，供视图函数调用"""
    @classmethod
    @log_auto
    def user_login(cls, request, **kwargs):
        """
        用户登录
        :param request: HttpRequest
        :param kwargs:
        :return:
        """
        login_data = LoginData(**kwargs)
        user = authenticate(username=login_data.job_id, password=login_data.password)
        if user:
            login(request, user)
            return user.user_info
        else:
            return None

    @classmethod
    @log_auto
    def get_user_info_by_job_id(cls, **kwargs):
        """根据job_id获得用户信息"""
        job_id_list = kwargs.get('job_id_list', None)
        res_queryset = User.objects.filter(job_id__in=job_id_list, is_deleted=False)
        if res_queryset:
            user_info_list = []
            for i in res_queryset:
                user_info_list.append(i.user_info)
            return True, tuple(user_info_list)
        return False, f'找不到用户'

    @classmethod
    @log_auto
    def set_user_workflow_admin_by_job_id(cls, **kwargs):
        """设置用户为工作流管理员"""
        data = SetWorkflow(**kwargs)
        user_queryset = User.objects.filter(job_id__in=data.job_id_list, is_deleted=False, user_type='common')
        if len(user_queryset) < len(data.job_id_list):
            return False, '部分用户工号不符合要求，请核实'
        for i in user_queryset:
            i.user_type = 'workflow_admin'
        User.objects.bulk_update(user_queryset, ['user_type'])
        return True, tuple(data.job_id_list)

    @classmethod
    @log_auto
    def set_common_by_job_id(cls, **kwargs):
        """设置工作流管理员为普通用户"""
        data = SetCommon(**kwargs)
        user_queryset = User.objects.filter(job_id__in=data.job_id_list, is_deleted=False, user_type='workflow_admin')
        if len(user_queryset) < len(data.job_id_list):
            return False, '部分用户工号不符合要求，请核实'
        for i in user_queryset:
            i.user_type = 'common'
        User.objects.bulk_update(user_queryset, ['user_type'])
        return True, tuple(data.job_id_list)

    @classmethod
    @log_auto
    def add_user(cls, **kwargs) -> tuple:
        """
        增加注册用户
        :param kwargs:
        :return:
        """
        data = AddUser(**kwargs)
        if User.objects.filter(job_id=data.job_id).exists():
            return False, '用户已存在'
        pwd_hash = make_password(data.password, None, 'pbkdf2_sha256')
        data = data.dict()
        data['password'] = pwd_hash
        user_obj = User(**data)
        user_obj.save()
        return True, dict(user_id=user_obj.id)

    @classmethod
    @log_auto
    def set_pwd(cls, request, **kwargs) -> tuple:
        """
        用户修改密码
        :param request:
        :param kwargs:
        :return:
        """
        data = SetPwd(**kwargs)
        if data.new_pwd_1 != data.new_pwd_2:
            return False, '两次密码不一致'
        user_job_id = request.user.job_id
        user = authenticate(username=user_job_id, password=data.old_pwd)
        if not user:
            return False, '原密码错误'
        new_pwd_f = make_password(data.new_pwd_1, None, hasher='pbkdf2_sha256')
        user.password = new_pwd_f
        user.save()
        return True, dict(job_id=user.job_id)

    @classmethod
    @log_auto
    def get_depart(cls, **kwargs):
        """
        分页获取部门信息
        :param kwargs:
        :return:
        """
        data = GetDepart(**kwargs)
        search_expression = Q(is_deleted=False)
        if data.search_value:
            search_expression &= Q(name__icontains=data.search_value)
        depart_queryset = Depart.objects.filter(search_expression)
        if not depart_queryset:
            return False, '查找不到部门'
        paginator = Paginator(depart_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list

        depart_info_result_list = []
        for i in target_page_obj_list:
            depart_info_result_list.append(i.depart_info)
        return True, dict(depart_info=depart_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def add_depart(cls, **kwargs):
        """
        增加部门
        :return:
        """
        data = AddDepart(**kwargs)
        if Depart.objects.filter(name=data.name, is_deleted=False).exists():
            return False, '部门已存在'
        depart_obj = Depart(name=data.name, parent_depart_id=data.parent_depart_id, creator_id=data.creator,
                              leader_id=data.leader_id, approver_id=data.approver_id)
        depart_obj.save()
        return True, dict(depart_id=depart_obj.id)

    @classmethod
    @log_auto
    def update_depart(cls, **kwargs):
        """
        更新部门
        :param depart_id:
        :param kwargs:
        :return:
        """
        data = UpdateDepart(**kwargs)
        depart_queryset = Depart.objects.filter(id=data.depart_id, is_deleted=False)
        if not depart_queryset:
            return False, '该部门不存在或已删除'
        depart_queryset.update(name=data.name, parent_depart_id=data.parent_depart_id, leader_id=data.leader_id,
                               approver_id=data.approver_id, creator_id=data.creator)
        return True, '更新完成'

    @classmethod
    @log_auto
    def delete_depart(cls, depart_id: int) -> tuple:
        """
        删除部门
        :param depart_id:
        :return:
        """
        depart_queryset = Depart.objects.filter(id=depart_id, is_deleted=False)
        if not depart_queryset:
            return False, '该部门不存在或已删除'
        depart_queryset.update(is_deleted=True)
        return True, '部门已删除'

    @classmethod
    @log_auto
    def get_depart_relate_user(cls, **kwargs):
        """
        获得指定部门内所有用户，分页
        :param kwargs:
        :return:
        """
        data = GetDepartRelateUser(**kwargs)
        try:
            depart_obj = Depart.objects.get(id=data.depart_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该部门不存在或者已删除'
        # all_relate_user_queryset = depart_obj.worker.filter()
        # all_relate_user_queryset = User.objects.filter(depart=depart_obj, belong_to_depart__is_delete=False)
        # 多对多且自定义中间表的时候，如何使用两端的关系查询同时又能根据中间表的字段进行过滤呢？
        all_relate_queryset = UserDepart.objects.filter(depart=depart_obj, is_deleted=False)
        all_relate_user_queryset = User.objects.filter(belong_to_depart__in=all_relate_queryset, is_deleted=False)
        if not all_relate_user_queryset:
            return False, '部门内没有用户'
        paginator = Paginator(all_relate_user_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list
        user_info_result_list = []
        for i in target_page_obj_list:
            user_info_result_list.append(i.user_info)
        return True, dict(relate_user_info=user_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def add_depart_relate_user(cls, **kwargs):
        """
        添加用户到指定部门
        :param kwargs:
        :return:
        """
        data = AddDepartRelateUser(**kwargs)
        try:
            depart_obj = Depart.objects.get(id=data.depart_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该部门不存在或者已删除'
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if len(user_queryset) < len(data.job_id):
            return False, '部分用户工号有误，请检查用户列表'
        middle_obj_list = []
        for u in user_queryset:
            middle_obj = UserDepart(user_id=u.id, depart=depart_obj, creator_id=data.creator) # creator需要统一，是用户外键
            middle_obj_list.append(middle_obj)
        UserDepart.objects.bulk_create(middle_obj_list)
        # 对于自定义的中间表：
        # 1.创建此类关系的唯一方法是创建中间模型的实例。
        # 2.不能使用add()，create()或者set()创建关系：
        # 简单说，需要我们自己手动往第三张表中添加两张表之间的关系
        # depart_obj.worker.add(user_queryset, through_defaults={'creator': data.creator}) 不能使用add

        return True, '用户已添加'

    @classmethod
    @log_auto
    def change_relation_of_user_and_depart(cls, **kwargs):
        """
        修改用户和部门之间关系（用户换部门）
        :param kwargs:
        :return:
        """
        data = ChangeRelationOfDepartAndUser(**kwargs)
        try:
            current_depart_obj = Depart.objects.get(id=data.depart_id, is_deleted=False)
            target_depart_obj = Depart.objects.get(id=data.new_depart_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, "部门不存在或已删除"
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if not user_queryset:
            return False, "用户不存在或已删除"
        user_id_list = []
        for u in user_queryset:
            user_id_list.append(u.id)
        middle_table_queryset = UserDepart.objects.filter(depart=current_depart_obj, user_id__in=user_id_list, is_deleted=False)

        for m in middle_table_queryset:
            m.depart = target_depart_obj
        UserDepart.objects.bulk_update(middle_table_queryset, ['depart'])
        return True, '用户所属部门已更新'


    @classmethod
    @log_auto
    def delete_user_from_depart(cls, **kwargs):
        """
        删除部门里的用户
        :param kwargs:
        :return:
        """
        data = DeleteUserFromDepart(**kwargs)
        try:
            depart_obj = Depart.objects.get(id=data.depart_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该部门不存在或者已删除'
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if not user_queryset:
            return False, "用户不存在或已删除"
        user_id_list = []
        for u in user_queryset:
            user_id_list.append(u.id)
        middle_table_queryset = UserDepart.objects.filter(depart=depart_obj, user_id__in=user_id_list, is_deleted=False)
        if len(middle_table_queryset) < len(data.job_id):
            return False, "部分用户在部门里不存在，核实后再删除"
        for m in middle_table_queryset:
            m.is_deleted = True
        UserDepart.objects.bulk_update(middle_table_queryset, ['is_deleted'])
        return True, "已删除部门内的用户"


    @classmethod
    @log_auto
    def get_jobtitle(cls, **kwargs):
        """
        分页返回所有岗位信息
        :param kwargs:
        :return:
        """
        data = GetJobtitle(**kwargs)
        search_expression = Q(is_deleted=False)
        if data.search_value:
            search_expression &= Q(name__icontains=data.search_value)
        job_queryset = JobTitle.objects.filter(search_expression)
        if not job_queryset:
            return False, '找不到岗位'
        paginator = Paginator(job_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list
        jobtitle_info_result_list = []
        for i in target_page_obj_list:
            jobtitle_info_result_list.append(i.jobtitle_info)
        return True, dict(jobtitle_info=jobtitle_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)


    @classmethod
    @log_auto
    def add_job(cls, **kwargs):
        """
        增加岗位
        :param kwargs:
        :return:
        """
        data = AddJob(**kwargs)
        if JobTitle.objects.filter(name=data.name, is_deleted=False).exists():
            return False, '岗位已存在'
        jobtitle_obj = JobTitle(name=data.name, creator_id=data.creator, description=data.description)
        jobtitle_obj.save()
        return True, dict(jobtitle_id=jobtitle_obj.id)


    @classmethod
    @log_auto
    def update_job(cls, **kwargs):
        """
        更新岗位
        :param jobtitle_id:
        :param kwargs:
        :return:
        """
        data = UpdateJob(**kwargs)
        jobtitle_queryset = JobTitle.objects.filter(id=data.jobtitle_id, is_deleted=False)
        if not jobtitle_queryset:
            return False, '该岗位不存在或已删除'
        jobtitle_queryset.update(name=data.name, creator_id=data.creator, description=data.description)
        return True, '更新完成'


    @classmethod
    @log_auto
    def delete_job(cls, jobtitle_id: int) -> tuple:
        """
        删除岗位
        :param depart_id:
        :return:
        """
        jobtitle_queryset = JobTitle.objects.filter(id=jobtitle_id, is_deleted=False)
        if not jobtitle_queryset:
            return False, '该岗位不存在或已删除'
        jobtitle_queryset.update(is_deleted=True)
        return True, '岗位已删除'

    @classmethod
    @log_auto
    def get_job_relate_user(cls, **kwargs):
        """
        获得指定岗位内所有用户，分页
        :param kwargs:
        :return:
        """
        data = GetJobRelateUser(**kwargs)
        try:
            job_obj = JobTitle.objects.get(id=data.jobtitle_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该岗位不存在或者已删除'
        # all_relate_user_queryset = job_obj.worker.all()
        all_relate_queryset = UserJob.objects.filter(job=job_obj, is_deleted=False)
        all_relate_user_queryset = User.objects.filter(perform_job__in=all_relate_queryset, is_deleted=False)
        if not all_relate_user_queryset:
            return False, '岗位内没有用户'
        paginator = Paginator(all_relate_user_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list
        user_info_result_list = []
        for i in target_page_obj_list:
            user_info_result_list.append(i.user_info)
        return True, dict(relate_user_info=user_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def add_job_relate_user(cls, **kwargs):
        """
        指定岗位里添加用户
        :param kwargs:
        :return:
        """
        data = AddJobRelateUser(**kwargs)
        try:
            jobtitle_obj = JobTitle.objects.get(id=data.jobtitle_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该岗位不存在或者已删除'
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if len(user_queryset) < len(data.job_id):
            return False, '部分用户工号有误，请检查用户列表'
        middle_obj_list = []
        for u in user_queryset:
            middle_obj = UserJob(user_id=u.id, job=jobtitle_obj, creator_id=data.creator)
            middle_obj_list.append(middle_obj)
        UserJob.objects.bulk_create(middle_obj_list)
        return True, '用户已添加'

    @classmethod
    @log_auto
    def change_relation_of_user_and_job(cls, **kwargs):
        """
        修改用户和岗位之间关系（用户换岗位）
        :param kwargs:
        :return:
        """
        data = ChangeRelationOfJobAndUser(**kwargs)
        try:
            current_jobtitle_obj = JobTitle.objects.get(id=data.jobtitle_id, is_deleted=False)
            target_jobtitle_obj = JobTitle.objects.get(id=data.new_jobtitle_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, "部门不存在或已删除"
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if not user_queryset:
            return False, "用户不存在或已删除"
        user_id_list = []
        for u in user_queryset:
            user_id_list.append(u.id)
        middle_table_queryset = UserJob.objects.filter(job=current_jobtitle_obj, user_id__in=user_id_list,
                                                          is_deleted=False)
        for m in middle_table_queryset:
            m.job = target_jobtitle_obj
        UserJob.objects.bulk_update(middle_table_queryset, ['job'])
        return True, '用户所属岗位已更新'


    @classmethod
    @log_auto
    def delete_user_from_job(cls, **kwargs):
        """
        删除岗位里的用户
        :param kwargs:
        :return:
        """
        data = DeleteUserFromJob(**kwargs)
        try:
            job_obj = JobTitle.objects.get(id=data.jobtitle_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, '该岗位不存在或者已删除'
        user_queryset = User.objects.filter(job_id__in=data.job_id, is_deleted=False)
        if not user_queryset:
            return False, "用户不存在或已删除"
        user_id_list = []
        for u in user_queryset:
            user_id_list.append(u.id)
        middle_table_queryset = UserJob.objects.filter(job=job_obj, user_id__in=user_id_list, is_deleted=False)
        if len(middle_table_queryset) < len(data.job_id):
            return False, "部分用户在部门里不存在，核实后再删除"
        for m in middle_table_queryset:
            m.is_deleted = True
        UserJob.objects.bulk_update(middle_table_queryset, ['is_deleted'])
        return True, "已删除岗位内的用户"





account_ins = AccountSupport()
