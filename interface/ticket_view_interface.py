
from pydantic import BaseModel
from typing import Literal, Optional
from interface.db_interface import *

class GetTicket(BaseModel):
    """查看工单列表"""
    state: Literal['ongoing', 'finish', 'reject', 'withdraw']
    apply_user_jobid: Optional[str]
    search_value: str = ''
    per_page: int = 10
    page: int = 1


class ApproveTicket(BaseModel):
    # user_id: int
    ticket_id: int

    suggestion: str
    approveresult: Literal['agree', 'reject', 'other']


class BeginNode(ApproveTicket):
    """开始节点处理函数需要的数据"""
    # user_id: Optional[int]
    # suggestion: Optional[str]
    # approveresult: Optional[Literal['agree', 'reject', 'other']]
    user_id: Optional[int]
    ticket_id: int
    suggestion: Optional[str]
    approveresult: Optional[Literal['agree', 'reject', 'other']]

class SerialNode(ApproveTicket):
    ticket_id: Optional[int]
    pass

class ParallelAllNode(ApproveTicket):
    ticket_id: Optional[int]
    pass

class ParallelAnyNode(ApproveTicket):
    ticket_id: Optional[int]
    pass

class ConditionNode(ApproveTicket):
    user_id: Optional[int]
    suggestion: Optional[str]
    approveresult: Optional[Literal['agree', 'reject', 'other']]

class EndNode(ApproveTicket):
    user_id: Optional[int]
    suggestion: Optional[str]
    approveresult: Optional[Literal['agree', 'reject', 'other']]

class SubmitTicket(BaseModel):
    """提交工单"""
    title: str
    # apply_user: int
    workflow_id: int
    # sn: str

    # now_node: int
    # is_adding_countersign: Optional[bool]
    # add_countersign_person: Optional[AddCountersignPerson]
    # temporary_approver: Optional[TemporaryApprover]
    # state: Literal['ongoing', 'finish', 'reject', 'withdraw']

    data: TicketData
    creator: int


class AddCountersign(BaseModel):
    """提交加签"""
    ticket_id: int
    temporary_countersign_jobid_list: List[str]

class TransferTicket(BaseModel):
    """转移工单"""
    ticket_id: int
    handover_jobid: str



