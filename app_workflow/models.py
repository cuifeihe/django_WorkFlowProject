import json

from django.db import models
from app_account.models import User, Depart, JobTitle
from common.basemodel import BaseModel


class WorkFlow(BaseModel):
    """流程模板表"""
    name = models.CharField(verbose_name='工作流名称', max_length=50, unique=True)
    description = models.CharField(verbose_name='工作流描述', max_length=200)

    able_to_cancel_approve = models.BooleanField(verbose_name='是否允许中途撤回审批', default=True)
    able_to_add_countersign = models.BooleanField(verbose_name='是否允许中途加签', default=True)
    able_to_transfer_approve = models.BooleanField(verbose_name='是否允许中途移交他人审批', default=True)

    submit_ticket_check = models.BooleanField(verbose_name='是否限制工单的提交申请', default=False)
    limit_expression = models.JSONField(verbose_name='限制工单提交的策略表达式', default=dict) # 需定义数据结构

    creator = models.ForeignKey(User, verbose_name='工作流创建人', related_name='create_workflow', on_delete=models.DO_NOTHING) # 工作流管理员创建

    @property
    def info(self):
        workflow_info = {'name': self.name, 'description': self.description}
        return workflow_info

class Node(BaseModel):
    """节点表，也是状态"""
    class NodeType(models.TextChoices):
        BEGIN = 'begin'
        SERIAL = 'serial'
        PARALLEL_ALL = 'parallel_all' # 并行会签
        PARALLEL_ANY = 'parallel_any' # 并行或签
        CONDITION = 'condition'
        END = 'end'

    class ParticipantType(models.TextChoices):
        ONE_PERSON = 'one_person' # 指定某一个人
        MULTI_PERSON = 'multi_person' # 并行，指定多个人
        DEPART = 'depart' # 指定部门，动态找到该部门的审批人进行审批
        ROLE = 'role' # 角色=部门+岗位，动态找到该部门、该岗位的人进行审批（只要是该部门、该岗位即可，不必一定为审批人）
        OTHER = 'other' # 开始节点、条件节点、结束节点，这种节点没有审批人

        # 缺点：
        # 不能支持跨部门角色指定，必须带上部门
        # 不能在多人节点下使用角色，多人审批时只能指定人

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, verbose_name='所属工作流', related_name='workflow_node')
    name = models.CharField(verbose_name='节点名称', max_length=20)

    order_id = models.IntegerField(verbose_name='节点编号', default=0)

    node_type = models.CharField(verbose_name='节点类型', choices=NodeType.choices, max_length=20, default=NodeType.BEGIN)
    participant_type = models.CharField(verbose_name='节点处理人类型', max_length=20, blank=True, null=True, choices=ParticipantType.choices,
                                        default=ParticipantType.ONE_PERSON)

    participant_one_person = models.ForeignKey(User, verbose_name='节点处理人-单人', on_delete=models.DO_NOTHING,
                                               null=True, blank=True, related_name='node_one_participant')
    participant_multi_person = models.ManyToManyField(User, verbose_name='节点处理人-多人',
                                                 related_name='node_multi_participant')
    participant_depart = models.ForeignKey(Depart, verbose_name='节点处理人-部门', on_delete=models.DO_NOTHING,
                                           null=True, blank=True, related_name='node_depart_participant')
    participant_role = models.JSONField(verbose_name='节点处理人-角色', default=dict)


    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_node', on_delete=models.DO_NOTHING)


    class Meta():
        ordering = ['id', 'order_id']
        unique_together = ['workflow', 'order_id']

    @property
    def participant(self):
        if self.participant_type == 'one_person':
            return '_' + self.participant_one_person.job_id

        elif self.participant_type == 'multi_person':
            participant_multi_person_jobid_list = []
            participant_queryset = User.objects.filter(node_multi_participant=self, is_deleted=False)
            for user in participant_queryset:
                participant_multi_person_jobid_list.append(user.job_id)
            return '_' + '_'.join(participant_multi_person_jobid_list)

        elif self.participant_type == 'depart':
            depart_obj = self.participant_depart
            user_queryset = User.objects.filter(depart_approver=depart_obj, is_deleted=False)
            return '_' + '_'.join([i.job_id for i in user_queryset])

        elif self.participant_type == 'role':
            role_data = json.loads(self.participant_role)
            depart_id = role_data.get('depart_id')
            jobtitle_id = role_data.get('jobtitle_id')
            depart_obj = Depart.objects.get(is_deleted=False, id=depart_id)
            jobtitle_obj = JobTitle.objects.get(is_deleted=False, id=jobtitle_id)
            user_queryset = User.objects.filter(depart_user=depart_obj, is_deleted=False, job_user=jobtitle_obj)
            return '_' + '_'.join([i.job_id for i in user_queryset])
        else:

            return ''
    @property
    def info(self):
        info = {'id': self.id, 'order_id': self.order_id, 'name': self.name, 'node_type': self.node_type, 'participant':self.participant}
        return info

class NodeRelation(BaseModel):
    """节点关系表。包含流程中两节点所有的可能，因此要写好条件结果"""
    class RelationType(models.TextChoices):
        AGREE = 'agree'
        REJECT = 'reject'
        CONDITION_RESULT_1 = 'count_compare_condition_result'
        CONDITION_RESULT_2 = 'right_or_wrong_condition_result'

    name = models.CharField(verbose_name='操作说明', max_length=50)
    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, verbose_name='所属工作流', related_name='workflow_node_relation')
    source_node = models.ForeignKey(Node, on_delete=models.CASCADE, verbose_name='源节点', related_name='source_node')
    destination_node = models.ForeignKey(Node, on_delete=models.CASCADE, verbose_name='目的节点', related_name='destination_node')

    relation = models.CharField(verbose_name='转换关系类型', max_length=50, choices=RelationType.choices)
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_noderelation', on_delete=models.DO_NOTHING)

    @property
    def info(self):
        info = {'id': self.id, 'source_and_destination': (self.source_node_id, self.destination_node_id),
                'relation_type': self.relation}
        return info

    class Meta():
        unique_together = ['workflow', 'name']


class CustomField(BaseModel):
    """自定义字段，工作流审批中的变量字段"""
    class CustomFieldType(models.TextChoices):
        """按自定义字段两种用途分为两种类型：数量关系比较、事实的对错区分；一个节点最多有一个自定义字段"""
        COUNT_COMPARE = 'count_compare'
        RIGHT_OR_WRONG = 'right_or_wrong'

    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, verbose_name='所属工作流', related_name='workflow_custom_field')

    field_name = models.CharField(verbose_name='自定义字段的名称', max_length=50)
    description = models.CharField(verbose_name='自定义字段描述', max_length=200)
    field_type = models.CharField(verbose_name='自定义字段类型', max_length=20, choices=CustomFieldType.choices)
    field_in_node = models.OneToOneField(Node, verbose_name='关联的条件节点', on_delete=models.DO_NOTHING, related_name='custom_field')

    critical_value_list = models.JSONField(verbose_name='数量比较字段_临界值列表', default=dict) # 定义数据结构
    compare_constant = models.JSONField(verbose_name='事实对错比较字段_常量', default=dict) # 定义数据结构

    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_customfield', on_delete=models.DO_NOTHING)

    @property
    def field_key(self):
        # 需要与前端一致，作为键用来传递用户工单中自定义字段的值
        return 'custom_field' + str(self.field_in_node.order_id)

    @property
    def info(self):
        info = {'fieled_name': self.field_name, 'field_key': self.field_key, 'field_in_node': self.field_in_node.id, 'field_type': self.field_type,
                'value_list': json.loads(self.critical_value_list) if self.field_type == 'count_compare' \
                    else json.loads(self.compare_constant)}

        return info

class ConditionResult(BaseModel):
    """使用自定义字段的判断条件的结果"""
    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, verbose_name='所属工作流', related_name='workflow_conditionresult')
    noderelation = models.OneToOneField(NodeRelation, verbose_name='所属节点关系', on_delete=models.DO_NOTHING, related_name='noderelation_conditionresult')

    low_bound = models.FloatField(verbose_name='数量比较字段_下边界值', blank=True, null=True, default=0) # 规定默认是0
    low_bound_is_close = models.BooleanField(verbose_name='下边界为闭区间', default=False, blank=True, null=True)
    up_bound = models.FloatField(verbose_name='数量比较字段_上边界值', blank=True, null=True, default=99999) # 规定默认是99999
    up_bound_is_close = models.BooleanField(verbose_name='上边界为闭区间', default=False, blank=True, null=True)

    condition_is_satisfied = models.BooleanField(verbose_name='事实成立的情况时', blank=True, null=True) # 一条记录的两个字段，最多只有一个为True
    condition_not_satisfied = models.BooleanField(verbose_name='事实不成立的情况时', blank=True, null=True)

    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_conditionresult', on_delete=models.DO_NOTHING)

    @property
    def info(self):
        info = {'noderelation_id': self.noderelation.id}

        if self.noderelation.relation == 'count_compare_condition_result':
            condition_result = dict(
                low_bound=self.low_bound, low_bound_is_close=self.low_bound_is_close,
                up_bound=self.up_bound, up_bound_is_close=self.up_bound_is_close)
            info['condition_result'] = condition_result # 类型报错？
        elif self.noderelation.relation == 'right_or_wrong_condition_result':
            condition_result = dict(
                condition_is_satisfied=self.condition_is_satisfied,
                condition_not_satisfied=self.condition_not_satisfied)
            info['condition_result'] = condition_result
        return info









# class WorkflowUserPermission(BaseModel):
#     """
#     用户，部门对工作流的操作权限。
#     view: 查看对应工单详情(不管该工作流是否开启查看权限校验)，
#     intervene:view+强制修改工单状态的权限。
#     admin:intervene + 可以修改工作流
#     """
#     app_workflow = models.ForeignKey(WorkFlow, on_delete=models.DO_NOTHING, verbose_name='所属工作流', related_name='workflow_permission')
#     permission = models.CharField(verbose_name='权限类型', max_length=100, null=True, blank=True)  # view, intervene， admin
#     user_type = models.CharField('用户类型', max_length=100, null=True, blank=True)  # user, department
#     user = models.CharField('用户', max_length=100, null=True, blank=True)  # username, department_id








