"""定义数据库中某些Json字段的格式"""
from typing import List, Literal, Union, Optional
from pydantic import BaseModel

class LimitCount(BaseModel):
    """限制次数"""
    period: int  # 限制周期({"period":24} 24小时),
    count: int  # 限制次数({"count":1}在限制周期内只允许提交1次),


class LimitPerson(BaseModel):
    """限制人员"""
    allow_person_id: Optional[int]  # 只允许特定人员提交
    allow_depart_id: Optional[int]  # 只允许特定部门提交
    allow_job_id: Optional[int]  # 只允许特定岗位提交


class WorkflowLimitExpression(BaseModel):
    """关于限制工单提交的策略"""
    limitcount: Optional[LimitCount]
    limitperson: Optional[LimitPerson]


class AddCountersignPerson(BaseModel):
    """加签人"""
    add_countersign_person: Optional[List[int]]


class TemporaryApprover(BaseModel):
    """被加签人"""
    temporary_approver: Optional[List[int]]


class Role(BaseModel):
    """角色"""
    depart_id: int
    jobtitle_id: int


class NodeParticipant(BaseModel):
    """节点中的处理人"""
    one_person: Optional[int]
    multi_person: Optional[int]       # Optional[List[int]]
    depart: Optional[int]
    role: Optional[Role]
    other: Optional[str]



class CustomFieldCriticalValueList(BaseModel):
    """自定义的数量比较字段的临界值"""
    critical_value: Optional[List[float]]


class CustomFieldCompareConstant(BaseModel):
    """自定义的事实判断字段的常量"""
    constant: Optional[List[str]]


class NodeResult(BaseModel):
    """某节点的处理结果"""
    job_id: str
    result: Literal['agree', 'reject', 'other']  # 最好联动数据库统一一下枚举
    node_order_id: int

class NowHandler(BaseModel):
    """工单中当前节点的处理人"""
    job_id_set: set[str]

class TicketNodeResult(BaseModel):
    """工单经历的所有节点的处理结果"""
    result_of_all_node: List[NodeResult]

class CustomField(BaseModel):
    """工单中自定义字段"""
    customfield_key: str # 与前端约定，使用'custom_field' + '_' + 当前条件节点的order_id
    customfield_value: Union[float, str]

class TicketData(BaseModel):
    """工单申请的原始数据"""
    # apply_person_id: int
    # apply_person_jobid: int
    # workflow_id: int
    workflow_name: str
    apply_cause: str
    custom_field: Optional[List[CustomField]] # 一个工单可能有多个自定义字段节点
