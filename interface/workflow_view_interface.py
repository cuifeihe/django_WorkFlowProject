
from pydantic import BaseModel
from typing import Literal, Optional, List, Union

from interface.db_interface import CustomFieldCriticalValueList, CustomFieldCompareConstant


class GetAllWorkflowInfo(BaseModel):
    """获取工作流大体信息"""
    search_value: str = ''
    per_page: int = 10
    page: int = 1

    user_id: int
    user_type: Literal['workflow_admin', 'super_admin']

class LimitCountAndPeriod(BaseModel):
    """限制次数"""
    limit_type: str = 'limit_count_and_period'
    period: int  # 限制周期({"period":24} 24小时),
    count: int  # 限制次数({"count":1}在限制周期内只允许提交1次),


class LimitPerson(BaseModel):
    """限制人员"""
    limit_type: str = 'limit_person'
    allow_type: Literal['jobid', 'depart', 'jobtitle']
    allow_jobid: Optional[List[str]]  # 只允许特定人员提交
    allow_depart_id: Optional[List[int]]  # 只允许特定部门提交
    allow_jobtitle_id: Optional[List[int]]  # 只允许特定岗位提交


class WorkflowLimitExpression(BaseModel):
    """关于限制工单提交的策略"""
    # limitcount: Optional[LimitCountAndPeriod]
    # limitperson: Optional[LimitPerson]
    limit_method: Union[LimitCountAndPeriod, LimitPerson]


class AddWorkflow(BaseModel):
    """增加一个工作流"""
    name: str
    description: str
    creator: int

    able_to_cancel_approve: Optional[bool] = True
    able_to_add_countersign: Optional[bool] = True
    able_to_transfer_approve: Optional[bool] = True
    view_permission_check: Optional[bool] = True
    submit_ticket_check: Optional[bool] = False
    limit_expression: Optional[WorkflowLimitExpression]


class Role(BaseModel):
    """角色"""
    depart: int
    job: int


class NodeParticipant(BaseModel):
    """节点中的处理人"""
    one_person: Optional[int]
    multi_person: Optional[List[str]]
    depart: Optional[int]
    role: Optional[Role]
    other: Optional[str]

class Node(BaseModel):
    """节点"""
    name: str
    # id: int
    node_type: Literal['begin', 'serial', 'parallel_all', 'parallel_any', 'condition', 'end']
    participant_type: Literal['one_person', 'multi_person', 'depart', 'role', 'other']
    participant: Optional[NodeParticipant]
    order_id: int # 同一工作流内不重复

class BranchOfCountCompare(BaseModel):
    """数量比较节点分支"""
    low_bound: float = 0
    low_bound_is_close: bool = False
    up_bound: float = 99999
    up_bound_is_close: bool = False

class BranchOfRightOrWrong(BaseModel):
    """事实判断节点分支"""
    condition_is_satisfied: bool
    condition_not_satisfied: bool

class ConditionResult(BaseModel):
    """自定义字段分支"""
    # node_relation_id: int # 关联的节点关系
    node_relation_name: str
    field_type: Literal['count_compare', 'right_or_wrong']

    condition_result_count_compare: Optional[BranchOfCountCompare]
    condition_result_right_or_wrong: Optional[BranchOfRightOrWrong]

class NodeRelation(BaseModel):
    """节点关系"""
    name: str # 同一工作流内不能重复
    source_node_id: int      # 应该是所属工作流节点的order_id
    destination_node_id: int # 应该是所属工作流节点的order_id
    relation: Literal['agree', 'reject', 'count_compare_condition_result', 'right_or_wrong_condition_result']

    # condition_result: Optional[ConditionResult]

class CustomField(BaseModel):
    """自定义字段"""
    field_name: str
    description: str
    field_type: Literal['count_compare', 'right_or_wrong']
    field_in_node: int # 应该是本工作流的order_id
    critical_value: Union[CustomFieldCriticalValueList, CustomFieldCompareConstant]# 需要验证器，与field_type相对应


class AddWorkflowDetail(BaseModel):
    """给目标工作流增加内容（节点、关系、字段）"""
    workflow_id: int
    creator: int
    node: List[Node]
    node_relation: List[NodeRelation] # 验证器

    custom_field: Optional[List[CustomField]]
    condition_result: Optional[List[ConditionResult]]

class SetWorkflowFunctionSwitch(BaseModel):
    """配置已有工作流的功能开关（是否允许中途撤回审批、是否允许中途加签、是否允许中途移交他人审批、是否限制工单的提交申请及何种限制方式）"""
    workflow_id: int
    # creator: int
    able_to_cancel_approve: bool
    able_to_add_countersign: bool
    able_to_transfer_approve: bool
    # view_permission_check: bool

    submit_ticket_check: bool
    limit_expression: Optional[WorkflowLimitExpression]


