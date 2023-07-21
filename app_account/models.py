from common.basemodel import BaseModel
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class UserManager(BaseUserManager):
    """用户管理器"""
    def create_user(self, name, job_id, email, phone, password, **kwargs):
        if not job_id:
            raise ValueError('用户必须填写工号')
        if not email:
            raise ValueError('用户必须填写邮箱')
        if not phone:
            raise ValueError('用户必须填写手机号')
        user = self.model(name=name, job_id=job_id, phone=phone, email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, name, password, phone, job_id, email, **kwargs):
        user = self.create_user(name=name, phone=phone, job_id=job_id, email=self.normalize_email(email), password=password, **kwargs)
        user.user_type = 'super_admin'
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin): # 继承这两个，不然用不了权限功能
    """用户表"""
    class UserType(models.TextChoices):
        """用户类型"""
        COMMON = 'common'
        WORKFLOW_ADMIN = 'workflow_admin'
        SUPER_ADMIN = 'super_admin'

    gender_enum = (('male', '男'),
                   ('female', '女'))

    name = models.CharField(verbose_name='姓名', max_length=30)
    job_id = models.CharField(verbose_name='工号', max_length=30, unique=True)
    email = models.EmailField(verbose_name='邮箱', max_length=100)
    phone = models.CharField(verbose_name='电话号码', max_length=13)
    gender = models.CharField(choices=gender_enum, max_length=8, verbose_name='性别')
    is_active = models.BooleanField(verbose_name='已激活', default=True)
    user_type = models.CharField(verbose_name='用户类型', choices=UserType.choices, max_length=20, default=UserType.COMMON)


    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建日期')
    update_time = models.DateTimeField(auto_now=True, verbose_name='最后更新日期')
    is_deleted = models.BooleanField(verbose_name='已删除', default=False)

    objects = UserManager()
    USERNAME_FIELD = 'job_id'
    REQUIRED_FIELDS = ['phone', 'name', 'email']

    @property
    def is_staff(self):
        return self.is_active

    def get_short_name(self):
        return self.name

    def get_alias_name(self):
        return self.job_id

    @property
    def user_info(self):
        user_info = {'name': self.name, 'job_id': self.job_id, 'email': self.email,
                       'phone': self.phone, 'gender': self.gender, 'user_type': self.user_type,
                       'depart_msg': self.relate_depart_msg, 'job_msg': self.relate_job_msg}
        return user_info

    @property
    def relate_depart_msg(self) -> tuple[dict]:
        """用户所在的部门id、部门名字，返回元组，包含字典；用户属于多个部门则包含多个字典"""
        relation_queryset = self.belong_to_depart.filter(is_deleted=False)
        user_dept_queryset = Depart.objects.filter(is_deleted=False, depart_include_user__in=relation_queryset)

        user_dept_id_list = []
        for i in user_dept_queryset:
            dept_msg = {'depart_id': i.id, 'depart_name': i.name}
            user_dept_id_list.append(dept_msg)
        return tuple(user_dept_id_list)

    @property
    def relate_job_msg(self) -> tuple:
        """用户所处的岗位id、岗位名字"""
        user_job_queryset = self.job_user.filter(is_deleted=False)
        user_job_id_list = []
        for i in user_job_queryset:
            res = dict(job_id=i.id, job_name=i.name)
            user_job_id_list.append(res)
        return tuple(user_job_id_list)

    @property
    def all_relate_parent_depart_msg(self) -> tuple:
        """查出用户所有的上级部门的id、部门名字"""
        res = []
        for i in self.relate_depart_msg:# 遍历用户所在部门的元组
            parent_depart_msg_list = [i]# 用户所在部门信息{id：， name：}先写进列表
            pk = i['depart_id']# 用户当前部门的id
            while True:
                parent_depart_msg = self.get_parent_depart_msg_by_son(pk)
                if not parent_depart_msg:# 如果当前部门没有父部门，跳出while
                    break
                parent_depart_msg_list.append(parent_depart_msg)#如果有，就查出父亲部门信息放进列表
                pk = parent_depart_msg['depart_id']
            res.append(tuple(parent_depart_msg_list))
        return tuple(res)

    def get_parent_depart_msg_by_son(self, son_depart_id):
        """根据子部门id获得其父部门的id、名字"""
        son_depart_obj = Depart.objects.get(id=son_depart_id)
        res = {}
        if son_depart_obj.parent_depart:
            res['depart_id'] = son_depart_obj.parent_depart_id
            res['depart_name'] = son_depart_obj.parent_depart.name
        return res

    def get_absolute_url(self):
        return f'app_account/index/{self.id}'

    class Meta():
        ordering = ['id']

class Depart(BaseModel):
    """部门表"""
    name = models.CharField(verbose_name='部门名称', max_length=50)
    # 本表作为 子部门 ，一个父部门具有多个子部门，因此子部门设外键，指向父部门
    parent_depart = models.ForeignKey("self", on_delete=models.DO_NOTHING, verbose_name='父部门', blank=True, null=True)

    leader = models.ForeignKey(User, verbose_name='部门领导', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='depart_leader')
    approver = models.ForeignKey(User, verbose_name='部门审批人', on_delete=models.DO_NOTHING, null=True, blank=True, related_name='depart_approver')

    worker = models.ManyToManyField(User, verbose_name='用户部门', related_name='depart_user', through='UserDepart', through_fields=('depart', 'user'))

    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_depart', on_delete=models.DO_NOTHING)

    class Meta():
        unique_together = ['name', 'parent_depart']
        ordering = ['id']

    @property
    def depart_info(self):
        depart_info = {}
        depart_info['name'] = self.name
        if self.leader:
            depart_info['leader'] = self.leader.job_id
        if self.approver:
            depart_info['approver'] = self.approver.job_id
        if self.parent_depart:
            depart_info['parent_depart'] = self.parent_depart.name

        return depart_info

class UserDepart(BaseModel):
    """用户、部门，多对多中间表（允许一个用户在一个部门里或多个部门里）"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name='员工', related_name='belong_to_depart')
    depart = models.ForeignKey(Depart, on_delete=models.DO_NOTHING, verbose_name='部门', related_name='depart_include_user')

    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_userdepart', on_delete=models.DO_NOTHING)


class JobTitle(BaseModel):
    """岗位表"""
    name = models.CharField(verbose_name='岗位名称', max_length=50)
    description = models.CharField(verbose_name='岗位描述', max_length=100, blank=True, null=True)

    worker = models.ManyToManyField(User, verbose_name='用户岗位', related_name='job_user', through='UserJob', through_fields=('job', 'user'))
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_jobtitle', on_delete=models.DO_NOTHING)

    @property
    def jobtitle_info(self):
        jobtitle_info = dict(name=self.name, description=self.description)
        return jobtitle_info

    class Meta():
        ordering = ['id']


class UserJob(BaseModel):
    """用户、岗位，多对多中间表（允许一个用户在一个岗位或多个岗位里）"""
    user = models.ForeignKey(User, verbose_name='员工', related_name='perform_job', on_delete=models.DO_NOTHING)
    job = models.ForeignKey(JobTitle, verbose_name='岗位', related_name='job_include_user', on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_userjob', on_delete=models.DO_NOTHING)


