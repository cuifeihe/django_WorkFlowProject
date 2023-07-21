import json

from django.db import models

from common.basemodel import BaseModel
from app_workflow.models import WorkFlow, Node, NodeRelation
from app_account.models import User


class Ticket(BaseModel):
    """工单表"""

    class TicketState(models.TextChoices):
        """工单整体状态"""
        ONGOING = 'ongoing'
        FINISH = 'finish'
        REJECT = 'reject'
        WITHDRAW = 'withdraw'

    title = models.CharField(verbose_name='工单标题', max_length=100)
    apply_user = models.ForeignKey(User, verbose_name='工单申请人', on_delete=models.DO_NOTHING, related_name='apply_ticket')
    workflow = models.ForeignKey(WorkFlow, on_delete=models.DO_NOTHING, verbose_name='所属工作流',
                                 related_name='workflow_ticket')
    sn = models.CharField(verbose_name='流水号', max_length=50)

    now_node = models.ForeignKey(Node, verbose_name='当前所处节点', on_delete=models.DO_NOTHING,
                                 related_name='ticket_now_node')

    is_adding_countersign = models.BooleanField(verbose_name='正在加签中', default=False)
    # add_countersign_person = models.JSONField(verbose_name='加签人', default=dict)
    temporary_approver = models.TextField(verbose_name='临时审批人', blank=True, null=True)  # 用text存储工号列表, 中间使用_分隔：'_001_002' （加签在形式上属于会签，需要所有加签人同意）

    now_handler = models.TextField(verbose_name='当前处理人的工号集合', blank=True, null=True) # 用text存储工号列表, 中间使用_分隔：'_001_002'

    state = models.CharField(verbose_name='工单进行状态', choices=TicketState.choices, max_length=30)

    results_of_all_nodes = models.JSONField(verbose_name='所有节点的处理结果', default=list)  # 定义数据结构

    data = models.JSONField(verbose_name='表单原始内容', default=dict)  # 定义数据结构
    creator = models.ForeignKey(User, verbose_name='创建人', related_name='create_ticket', on_delete=models.DO_NOTHING)

    @property
    def info(self):
        info = {
            'title': self.title, 'apply_user': self.apply_user_id, 'workflow_id': self.workflow_id, 'sn': self.sn,
            'now_node': self.now_node_id, 'state': self.state,
            'results_of_all_nodes': self.results_of_all_nodes,
            'data': json.loads(self.data)
        }

        return info

    class Meta():
        ordering = ['id', 'workflow', 'title']


class TicketDetail(BaseModel):
    """工单详细流水表"""

    class ApproveResult(models.TextChoices):
        AGREE = 'agree'
        REJECT = 'reject'
        OTHER = 'other'

    ticket = models.ForeignKey(Ticket, verbose_name='所属工单', on_delete=models.DO_NOTHING, related_name='detail')
    suggestion = models.CharField(verbose_name='处理意见', max_length=100)
    approveresult = models.CharField(verbose_name='审批结果', choices=ApproveResult.choices, max_length=20)
    # 临时加签不改变工作流模板状态
    is_temporary_countersign = models.BooleanField(verbose_name='是否属于临时加签', default=False)

    transactor = models.ForeignKey(User, verbose_name='办理人', on_delete=models.DO_NOTHING, related_name='transact_ticket_detail')


