import datetime
import json
from typing import Callable

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q

from app_account.models import User
from app_ticket.models import Ticket, TicketDetail
from app_workflow.models import Node, NodeRelation, WorkFlow, CustomField, ConditionResult
from common.decorators import log_auto
from interface.ticket_view_interface import GetTicket, SerialNode, ParallelAllNode, ParallelAnyNode, \
    ApproveTicket, SubmitTicket, AddCountersign, TransferTicket


class TicketSupport(object):
    """工单管理相关方法，供视图函数调用"""
    # 状态(节点)、状态处理函数的对应关系字典
    RELATION_OF_NODE_TYPE_AND_FUNCTION = {
        'begin': 'begin_node_handle_function',
        'serial': 'serial_node_handle_function',
        'parallel_all': 'parallel_all_node_handle_function',
        'parallel_any': 'parallel_any_node_handle_function',
        'condition': 'condition_node_handle_function',
        'end': 'end_node_handle_function'
    }

    @classmethod
    @log_auto
    def dispatch_node_and_function(cls, node_function_map: dict, node_type: str) -> tuple[bool, [str, Callable]]:
        """状态（节点）和处理函数之间的分发函数"""
        if not hasattr(cls, node_function_map.get(node_type)):
            return False, '没有对应的处理函数'
        target_func = getattr(cls, node_function_map.get(node_type))
        return True, target_func

    @classmethod
    @log_auto
    def get_ticket(cls, **kwargs):
        """工作流管理员使用，检索获取工单信息"""
        data = GetTicket(**kwargs)
        search_expression = Q(is_deleted=False, state=data.state)
        if data.search_value:
            search_expression &= Q(title__icontains=data.search_value)
        if data.apply_user_jobid:
            user_obj = User.objects.filter(job_id=data.apply_user_jobid, is_deleted=False).first()
            if user_obj:
                search_expression &= Q(apply_user_id=user_obj.id)

        ticket_queryset = Ticket.objects.filter(search_expression)
        if not ticket_queryset:
            return False, '找不到工单'
        paginator = Paginator(ticket_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list
        ticket_info_result_list = []
        for i in target_page_obj_list:
            ticket_info_result_list.append(i.info)
        return True, dict(ticket_info=ticket_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def need_approve_ticket(cls, user_obj):
        """用户登录后获得待自己审批的工单"""
        # 考虑当前处于加签状态
        target_ticket = Ticket.objects.filter(
            Q(is_deleted=False, is_adding_countersign=False, now_handler__contains=user_obj.job_id, state='ongoing') |
            Q(is_deleted=False, is_adding_countersign=True, temporary_approver__contains=user_obj.job_id,
              state='ongoing'))
        if not target_ticket:
            return True, '暂无您的待审批工单'
        approve_ticket_list = [ticket.info for ticket in target_ticket]
        return True, tuple(approve_ticket_list)

    @classmethod
    @log_auto
    def get_target_index_from_list(cls, data_list: list[dict], target_key, target_value) -> int:
        """从一个以固定字典结构为元素的列表中，根据给定字典的键及对应的值，获得该字典在列表中的位置"""
        for i, content in enumerate(data_list):
            if target_key in content:
                if content.get(target_key) == target_value:
                    return i

    @classmethod
    @log_auto
    def judge_condition_and_get_next_node(cls, ticket_obj: Ticket):
        """假设当前处于条件节点，根据用户提交工单内容和工作流，需要判断出下一个节点并返回节点id"""
        current_condition_node_obj = Node.objects.filter(ticket_now_node=ticket_obj, is_deleted=False).first()
        user_submit_custom_field_value_list = (json.loads(ticket_obj.data)).get('custom_field')
        # 与前端约定，使用'custom_field' + '_' + 当前条件节点的order_id作为自定义字段的值的标识的值
        custom_field_key = 'custom_field_' + str(current_condition_node_obj.order_id)
        custom_field_index = cls.get_target_index_from_list(user_submit_custom_field_value_list, 'customfield_key',
                                                            custom_field_key)
        if custom_field_index is None:
            return False, '工单内用户提交信息不全，自定义字段的值缺失'
        custom_field_user_value = user_submit_custom_field_value_list[custom_field_index].get('customfield_value',
                                                                                              None)  # 用户工单实际参数值
        node_relation_queryset = NodeRelation.objects.filter(source_node=current_condition_node_obj, is_deleted=False)
        relation_type = node_relation_queryset.first().relation
        node_relation_id_list = [node_relation.id for node_relation in node_relation_queryset]
        if relation_type == 'count_compare_condition_result':  # 数量比较的条件
            custom_field_obj = CustomField.objects.filter(field_in_node=current_condition_node_obj,
                                                          is_deleted=False).first()
            critical_value_list = (
                json.loads(custom_field_obj.critical_value_list).get('critical_value')).copy()  # 获得工作流定义的该处自定义字段的临界值列表
            condition_result_queryset = ConditionResult.objects.filter(noderelation_id__in=node_relation_id_list,
                                                                       is_deleted=False)
            # 先判断用户实际值是否与临界值重合
            if custom_field_user_value in critical_value_list:
                condition_result_obj = condition_result_queryset.filter(
                    Q(up_bound=custom_field_user_value, up_bound_is_close=True, is_deleted=False) |
                    Q(low_bound=custom_field_user_value, low_bound_is_close=True, is_deleted=False)).first()
                next_node_id = condition_result_obj.noderelation.destination_node_id
                return True, next_node_id

            else:  # 不重合，需要排序确定位置，分情况是否最小或者最大
                if len(critical_value_list) == 1:  # 仅有一个临界值的情况
                    if custom_field_user_value < critical_value_list[0]:
                        condition_result_obj = condition_result_queryset.filter(up_bound=critical_value_list[0],
                                                                                is_deleted=False).first()
                        next_node_id = condition_result_obj.noderelation.destination_node_id
                        return True, next_node_id
                    elif custom_field_user_value > critical_value_list[0]:
                        condition_result_obj = condition_result_queryset.filter(low_bound=critical_value_list[0],
                                                                                is_deleted=False).first()
                        next_node_id = condition_result_obj.noderelation.destination_node_id
                        return True, next_node_id
                elif len(critical_value_list) > 1:  # 多个临界值
                    critical_value_list.append(custom_field_user_value)
                    critical_value_list.sort()
                    if critical_value_list.index(custom_field_user_value) == 0:  # 用户值如果是最小值
                        condition_result_obj = condition_result_queryset.filter(up_bound=critical_value_list[1],
                                                                                is_deleted=False).first()
                        next_node_id = condition_result_obj.noderelation.destination_node_id
                        return True, next_node_id
                    elif critical_value_list.index(custom_field_user_value) == (len(critical_value_list) - 1):  # 如果是最大值
                        condition_result_obj = condition_result_queryset.filter(low_bound=critical_value_list[-2],
                                                                                is_deleted=False).first()
                        next_node_id = condition_result_obj.noderelation.destination_node_id
                        return True, next_node_id
                    else:  # 如果不是极值
                        index = critical_value_list.index(custom_field_user_value)
                        condition_result_obj = condition_result_queryset.filter(
                            low_bound=critical_value_list[index - 1],
                            up_bound=critical_value_list[index + 1],
                            is_deleted=False).first()
                        next_node_id = condition_result_obj.noderelation.destination_node_id
                        return True, next_node_id

        elif relation_type == 'right_or_wrong_condition_result':
            """是非判断的条件"""
            custom_field_obj = CustomField.objects.filter(field_in_node=current_condition_node_obj,
                                                          is_deleted=False).first()
            constant_list = (
                json.loads(custom_field_obj.compare_constant).get('constant')).copy()  # 获得工作流定义的该处自定义字段的常量列表
            condition_result_queryset = ConditionResult.objects.filter(noderelation_id__in=node_relation_id_list,
                                                                       is_deleted=False)
            if custom_field_user_value in constant_list:
                condition_result_obj = condition_result_queryset.filter(condition_is_satisfied=True,
                                                                        is_deleted=False).first()
                next_node_id = condition_result_obj.noderelation.destination_node_id
                return True, next_node_id
            else:
                condition_result_obj = condition_result_queryset.filter(condition_not_satisfied=True,
                                                                        is_deleted=False).first()
                next_node_id = condition_result_obj.noderelation.destination_node_id
                return True, next_node_id
        else:
            pass

    @classmethod
    @log_auto
    def get_ticket_next_node_from_current_node(cls, ticket_obj: Ticket):
        """给定工单，根据工单的当前节点获得下一节点；工单初始提交后自动执行一次"""
        current_node_obj = Node.objects.filter(ticket_now_node=ticket_obj, is_deleted=False).first()
        workflow_obj = WorkFlow.objects.filter(workflow_ticket=ticket_obj, is_deleted=False).first()
        next_node_queryset = NodeRelation.objects.filter(workflow=workflow_obj, source_node=current_node_obj,
                                                         is_deleted=False)
        if not next_node_queryset:  # 当前为end节点
            return False, '当前已经为END节点了，没有下一节点了'

        if len(next_node_queryset) == 1:  # 当前节点不是条件节点，下一节点只有一个
            next_node_id = next_node_queryset.first().destination_node_id
            return True, next_node_id

        elif len(next_node_queryset) > 1:  # 当前为条件节点，下一节点才有多个，正常的话此处不会出现这种情况（当前为条件节点时不会调用本函数）
            return False, '参数有误'
            pass

    @classmethod
    @log_auto
    def judge_node_is_condition_type_from_node_id(cls, node_id):
        """根据node_id判断节点是不是条件节点。"""
        node_obj = Node.objects.get(id=node_id, is_deleted=False)
        if node_obj.node_type == 'condition':
            return True  # '该节点是条件节点'
        else:
            return False  # '该节点不是条件节点'

    @classmethod
    @log_auto
    def judge_node_is_end_type_from_node_id(cls, node_id):
        """根据node_id判断节点是不是结束节点"""
        node_obj = Node.objects.get(id=node_id, is_deleted=False)
        if node_obj.node_type == 'end':
            return True  # '该节点是结束节点'
        else:
            return False  # '该节点不是结束节点'

    @classmethod
    @log_auto
    def update_ticket_if_agree(cls, ticket_obj: Ticket, user_obj: User, approveresult, next_node_id):
        """审批同意之后的操作"""
        history_result_list = (ticket_obj.results_of_all_nodes).copy()
        next_node_obj = Node.objects.get(id=next_node_id, is_deleted=False)
        update_data = {
            'job_id': user_obj.job_id,
            'result': approveresult,
            'node_order_id': ticket_obj.now_node.order_id,
        }
        history_result_list.append(update_data)
        ticket_obj.results_of_all_nodes = (history_result_list)
        ticket_obj.now_node_id = next_node_id
        ticket_obj.now_handler = next_node_obj.participant
        ticket_obj.save()
        # 判断后续节点的情况：
        # 判断接下来是不是要到了END节点，是就直接执行END
        is_end_node = cls.judge_node_is_end_type_from_node_id(next_node_id)
        if is_end_node:
            handle_func = getattr(cls, cls.RELATION_OF_NODE_TYPE_AND_FUNCTION['end'])
            flag, result = handle_func(ticket_obj)
            if not flag:
                return flag, result
        # 判断是不是到了条件节点，是则直接再推向下一节点; 不能将条件节点呈现出来，需要系统自动处理；
        is_condition_node = cls.judge_node_is_condition_type_from_node_id(next_node_id)
        if is_condition_node:
            handle_func = getattr(cls, cls.RELATION_OF_NODE_TYPE_AND_FUNCTION['condition'])
            flag, result = handle_func(ticket_obj)
            if not flag:
                return flag, result
        return True, '审批同意，节点已更新'

    @classmethod
    @log_auto
    def update_ticket_if_reject(cls, ticket_obj, user_obj: User, approveresult):
        """审批拒绝之后的操作"""
        ticket_obj.state = 'reject'
        history_result_list = (ticket_obj.results_of_all_nodes)
        updata_data = {
            'job_id': user_obj.job_id,
            'result': approveresult,
            'node_order_id': ticket_obj.now_node.order_id,
        }
        history_result_list.append(updata_data)
        ticket_obj.results_of_all_nodes = history_result_list
        ticket_obj.save()

    # 节点处理函数，需要在运行前进行相应检查
    @classmethod
    @log_auto
    def begin_node_handle_function(cls, ticket_obj: Ticket):
        """开始节点，新工单完成提交后要自动执行"""
        flag, next_node_id = cls.get_ticket_next_node_from_current_node(ticket_obj)  # 当前为begin节点
        if not flag:
            return False, '参数错误'
        # 判断 next_node_id 是否是条件节点
        next_is_condition = cls.judge_node_is_condition_type_from_node_id(next_node_id)
        if next_is_condition:  # begin后面是条件节点，需要自动判断条件并更新到下一节点
            ticket_obj.now_node_id = next_node_id
            ticket_obj.save()
            dispatch_flag, handle_func = cls.dispatch_node_and_function(cls.RELATION_OF_NODE_TYPE_AND_FUNCTION,
                                                                        'condition')
            if dispatch_flag:
                handle_flag, res_condition = handle_func(ticket_obj)
                return handle_flag, res_condition
            return dispatch_flag, handle_func

        else:  # begin后面不是条件节点，则更新工单中的 now_node 和 now_handler
            next_node_obj = Node.objects.get(id=next_node_id, is_deleted=False)
            ticket_obj.now_node = next_node_obj
            ticket_obj.now_handler = next_node_obj.participant
            ticket_obj.save()

        return True, '工单初始化完成'

    @classmethod
    @log_auto
    def serial_node_handle_function(cls, user_obj: User, ticket_obj: Ticket, **kwargs):
        """如果当前是串行节点，处理函数"""
        data = SerialNode(**kwargs)
        ticket_detail_obj = TicketDetail(ticket=ticket_obj, suggestion=data.suggestion,
                                         approveresult=data.approveresult,
                                         transactor_id=user_obj.id)
        ticket_detail_obj.save()
        if data.approveresult == 'agree':  # 同意，获得下一节点，写入Ticket表成为当前节点
            next_node_flag, next_node_id = cls.get_ticket_next_node_from_current_node(ticket_obj)
            if next_node_flag:
                flag, res = cls.update_ticket_if_agree(ticket_obj, user_obj, 'agree', next_node_id)
                return flag, res
            else:
                return False, next_node_id
        elif data.approveresult == 'reject':
            cls.update_ticket_if_reject(ticket_obj, user_obj, 'reject')
            return True, '串行节点审批完成（拒绝）'

    @classmethod
    @log_auto
    def parallel_all_node_handle_function(cls, user_obj: User, ticket_obj: Ticket, **kwargs):
        """当前是并行会签节点，且需所有审批人同意才行"""
        data = ParallelAllNode(**kwargs)
        # 获得当前所有审批人；进行审批；查看其他人是否也审批完及审批结果，决定是否推向下一节点，或者维持在当前节点；
        now_node_approver_jobid_list = (ticket_obj.now_handler[1:]).split('_')

        # now_node_approver_queryset = User.objects.filter(job_id__in=now_node_approver_jobid_list,
        #                                                  is_deleted=False)
        # now_node_approver_id_list = [i.id for i in now_node_approver_queryset]

        ticket_detail_obj = TicketDetail(ticket=ticket_obj, suggestion=data.suggestion,
                                         approveresult=data.approveresult,
                                         transactor=user_obj)
        ticket_detail_obj.save()

        if data.approveresult == 'agree':
            # ticket_detail_obj_history = TicketDetail.objects.filter(ticket=ticket_obj, approveresult='agree',
            #                                                         transactor_id__in=now_node_approver_id_list)
            # if len(ticket_detail_obj_history) == len(now_node_approver_jobid_list):
            if len(now_node_approver_jobid_list) == 1:
                """当前节点处理人只剩一个，说明其余通过， 推向下一节点"""
                next_node_flag, next_node_id = cls.get_ticket_next_node_from_current_node(ticket_obj)
                if next_node_flag:
                    flag, res = cls.update_ticket_if_agree(ticket_obj, user_obj, 'agree', next_node_id)
                    return flag, res
                else:
                    return False, next_node_id
            else:
                """有其他人没有审批，不能推向下一节点，维持原节点不动"""
                history_result_list = ticket_obj.results_of_all_nodes
                updata_data = {
                    'job_id': user_obj.job_id,
                    'result': 'agree',
                    'node_order_id': ticket_obj.now_node.order_id,
                }
                history_result_list.append(updata_data)
                ticket_obj.results_of_all_nodes = history_result_list
                # handler_job_id_list = ticket_obj.now_handler[1:].split('_')
                now_node_approver_jobid_list.remove(user_obj.job_id)
                ticket_obj.now_handler = '_' + '_'.join(now_node_approver_jobid_list)
                ticket_obj.save()
                return True, '您已完成审批，请等待其他人的审批结果'

        elif data.approveresult == 'reject':
            cls.update_ticket_if_reject(ticket_obj, user_obj, 'reject')
            return True, '串行节点审批完成（已拒绝）'
        else:
            pass

    @classmethod
    @log_auto
    def parallel_any_node_handle_function(cls, user_obj: User, ticket_obj: Ticket, **kwargs):
        """当前是并行或签节点，且需其中一个审批人同意就行"""
        data = ParallelAnyNode(**kwargs)
        ticket_detail_obj = TicketDetail(ticket=ticket_obj, suggestion=data.suggestion,
                                         approveresult=data.approveresult,
                                         transactor=user_obj)
        ticket_detail_obj.save()

        if data.approveresult == 'agree':
            next_node_flag, next_node_id = cls.get_ticket_next_node_from_current_node(ticket_obj)
            if next_node_flag:
                flag, res = cls.update_ticket_if_agree(ticket_obj, user_obj, 'agree', next_node_id)
                return flag, res
            else:
                return False, next_node_id

        elif data.approveresult == 'reject':
            cls.update_ticket_if_reject(ticket_obj, user_obj, 'reject')
            return True, '串行节点审批完成（拒绝）'
        else:
            pass

    @classmethod
    @log_auto
    def condition_node_handle_function(cls, ticket_obj: Ticket):
        """当前为条件节点，处理函数:"""
        while True:  # 如果多个条件节点相连，应该自动执行到最后一个条件节点，直至一个非条件节点
            flag, next_node_id = cls.judge_condition_and_get_next_node(ticket_obj)
            if flag:
                is_condition_node = cls.judge_node_is_condition_type_from_node_id(next_node_id)
                if not is_condition_node:
                    next_node_obj = Node.objects.get(id=next_node_id, is_deleted=False)
                    ticket_obj.now_node_id = next_node_id
                    ticket_obj.now_handler = next_node_obj.participant
                    ticket_obj.save()
                    break
                else:
                    ticket_obj.now_node_id = next_node_id
                    ticket_obj.save()
            else:
                return flag, next_node_id
        return True, '已向下推进，直至不是条件节点'

    @classmethod
    @log_auto
    def end_node_handle_function(cls, ticket_obj):
        """如果当前节点为end，说明所有审批均已同意"""
        ticket_obj.state = 'finish'
        ticket_obj.save()
        return True, '所有环节已审批完成'

    @classmethod
    @log_auto
    def countersign_handle_function(cls, user_obj: User, ticket_obj: Ticket, **kwargs):
        """处理加签中的工单（允许有多个临时加签人，且需经所有人同意才行，处理逻辑类似于并行会签）"""
        data = ParallelAllNode(**kwargs)
        ticket_detail_obj = TicketDetail(ticket=ticket_obj, suggestion=data.suggestion,
                                         approveresult=data.approveresult, is_temporary_countersign=True,
                                         transactor=user_obj)
        ticket_detail_obj.save()

        if data.approveresult == 'agree':
            # ticket_detail_obj_history = TicketDetail.objects.filter(ticket=ticket_obj, approveresult='agree',
            #                                                         is_temporary_countersign=True)
            temporary_approver_jobid_list = ticket_obj.temporary_approver[1:].split('_')
            if len(temporary_approver_jobid_list) == 1:
                ticket_obj.is_adding_countersign = False
                history_result_list = ticket_obj.results_of_all_nodes
                updata_data = {
                    'job_id': user_obj.job_id,
                    'result': 'agree',
                    'node_order_id': 'temporary_node',
                }
                history_result_list.append(updata_data)
                ticket_obj.results_of_all_nodes = history_result_list
                ticket_obj.save()
                return True, '所有加签人已审批通过'
            else:
                temporary_approver_jobid_list.remove(user_obj.job_id)
                ticket_obj.temporary_approver = '_' + '_'.join(temporary_approver_jobid_list)
                history_result_list = ticket_obj.results_of_all_nodes
                updata_data = {
                    'job_id': user_obj.job_id,
                    'result': 'agree',
                    'node_order_id': 'temporary_node',
                }
                history_result_list.append(updata_data)
                ticket_obj.results_of_all_nodes = history_result_list
                ticket_obj.save()
                return True, '您已完成加签审批，请等待其他加签人完成审批'
            pass
        elif data.approveresult == 'reject':
            ticket_obj.state = 'reject'
            history_result_list = ticket_obj.results_of_all_nodes
            updata_data = {
                'job_id': user_obj.job_id,
                'result': 'reject',
                'node_order_id': 'temporary_node',
            }
            history_result_list.append(updata_data)
            ticket_obj.results_of_all_nodes = history_result_list

            ticket_obj.save()
            return True, '加签人审批拒绝了工单，流程结束'
        else:
            pass

    @classmethod
    @log_auto
    def approve_ticket(cls, user_obj: User, **kwargs):
        """进行单据审批动作
        必须参数：工单id（url参数内）（工单当前节点信息）、处理意见、处理结果（post请求）
        需要：节点状态、状态处理函数、处理前检查函数 三者对应关系；处理之后的状态变化；相关结果写回数据库
        """
        data = ApproveTicket(**kwargs)
        try:
            ticket_obj = Ticket.objects.get(id=data.ticket_id, is_deleted=False, state='ongoing')
        except ObjectDoesNotExist:
            return False, '用户提交信息有误，找不到对应的工单'

        if ticket_obj.is_adding_countersign:  # 如果当前处于加签状态
            now_handler_jobid_list = ticket_obj.temporary_approver[1:].split('_')
            if user_obj.job_id not in now_handler_jobid_list:
                return False, '您并非此工单的当前处理人'
            flag, res = cls.countersign_handle_function(user_obj, ticket_obj, **(data.dict()))
            return flag, res

        else:  # 如果当前不是加签状态
            now_handler_jobid_list = ticket_obj.now_handler[1:].split('_')
            if user_obj.job_id not in now_handler_jobid_list:
                return False, '您并非此工单的当前处理人'
            handle_func_flag, handle_func = cls.dispatch_node_and_function(cls.RELATION_OF_NODE_TYPE_AND_FUNCTION,
                                                                           ticket_obj.now_node.node_type)
            if not handle_func_flag:
                return False, '参数错误'
            flag, result = handle_func(user_obj, ticket_obj, **(data.dict()))  # 三种状态处理函数（串行、并行会签、并行或签）
            return flag, result

    @classmethod
    @log_auto
    def submit_ticket(cls, user_obj: User, **kwargs):
        """工单提交页面"""
        data = SubmitTicket(**kwargs)
        try:
            workflow_obj = WorkFlow.objects.get(id=data.workflow_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, "使用的工作流模板不存在或者已删除"
        # 检测提交的限制策略
        if workflow_obj.submit_ticket_check:
            limit_data = json.loads(workflow_obj.limit_expression).get('limit_method')
            if limit_data.get('limit_type') == 'limit_count_and_period':
                now_time = datetime.datetime.now()
                period = limit_data.get('period')
                deadline = now_time - datetime.timedelta(hours=period)
                last_ticket_queryset = Ticket.objects.filter(creator_id=data.creator, is_deleted=False,
                                                             workflow=workflow_obj, create_time__gte=deadline)
                if not last_ticket_queryset.exists():
                    pass
                else:
                    if len(last_ticket_queryset) >= limit_data.get('count'):
                        return False, '工单提交受限制'
            elif limit_data.get('limit_type') == 'limit_person':
                if limit_data.get('allow_type') == 'jobid':
                    if user_obj.job_id not in limit_data.get('allow_jobid'):
                        return False, '工单提交受限制'
                elif limit_data.get('allow_type') == 'depart':
                    if {i.get("depart_id") for i in user_obj.relate_depart_msg}.isdisjoint(
                            set(limit_data.get('allow_depart_id'))):  # 集合无交集
                        return False, '工单提交受限制'
                elif limit_data.get('allow_type') == 'jobtitle':
                    if {i.get("job_id") for i in user_obj.relate_job_msg}.isdisjoint(
                            set(limit_data.get('allow_jobtitle_id'))):
                        return False, '工单提交受限制'

            else:
                return False, '工作流的限制提交表达式有误，请联系管理员'
        begin_node_obj = Node.objects.get(is_deleted=False, workflow=workflow_obj, node_type='begin')
        ticket_obj = Ticket(title=data.title, apply_user_id=data.creator,
                            workflow_id=data.workflow_id,
                            sn=cls.get_sn(data.workflow_id, data.creator, 'TK'),
                            now_node_id=begin_node_obj.id,
                            state='ongoing',
                            data=data.data.json(),
                            creator_id=data.creator)
        ticket_obj.save()
        flag, handle_func = cls.dispatch_node_and_function(cls.RELATION_OF_NODE_TYPE_AND_FUNCTION, 'begin')
        if flag:
            return handle_func(ticket_obj)

    @classmethod
    @log_auto
    def get_sn(cls, workflow_id, job_id, code_prefix):
        """生成SN码"""
        code_prefix = str(code_prefix)
        if len(code_prefix) > 10:
            code_prefix = code_prefix[-10::1]
        code_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        code_workflow = str(workflow_id).zfill(5)
        code_jobid = str(job_id).zfill(10)
        return code_prefix + code_time + code_workflow + code_jobid

    @classmethod
    @log_auto
    def user_get_ticket(cls, get_type, user: User, per_page, page):
        """用户获得自己提交或者审批过的工单"""
        if get_type == 'my_submit':
            ticket_queryset = Ticket.objects.filter(creator_id=user.id, is_deleted=False)
            if not ticket_queryset:
                return False, '找不到工单'
            paginator = Paginator(ticket_queryset, per_page)
            try:
                target_page_result = paginator.page(page)
            except PageNotAnInteger:
                target_page_result = paginator.page(1)
            except EmptyPage:
                target_page_result = paginator.page(paginator.num_pages)
            target_page_obj_list = target_page_result.object_list
            ticket_info_result_list = []
            for i in target_page_obj_list:
                ticket_info_result_list.append(i.info)
            return True, dict(ticket_info=ticket_info_result_list,
                              per_page=per_page, page=page, total_obj=paginator.count)

        elif get_type == 'my_approve':
            ticket_detail_queryset = TicketDetail.objects.filter(transactor_id=user.id, is_deleted=False)
            if not ticket_detail_queryset:
                return False, '找不到工单'
            ticket_id_set = {i.ticket_id for i in ticket_detail_queryset}
            ticket_queryset = Ticket.objects.filter(id__in=ticket_id_set, is_deleted=False)
            if not ticket_queryset:
                return False, '找不到工单'
            paginator = Paginator(ticket_queryset, per_page)
            try:
                target_page_result = paginator.page(page)
            except PageNotAnInteger:
                target_page_result = paginator.page(1)
            except EmptyPage:
                target_page_result = paginator.page(paginator.num_pages)
            target_page_obj_list = target_page_result.object_list
            ticket_info_result_list = []
            for i in target_page_obj_list:
                ticket_info_result_list.append(i.info)
            return True, dict(ticket_info=ticket_info_result_list,
                              per_page=per_page, page=page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def add_countersign(cls, user_obj: User, **kwargs):
        data = AddCountersign(**kwargs)
        ticket_queryset = Ticket.objects.filter(id=data.ticket_id, is_deleted=False, state='ongoing')
        if not ticket_queryset.exists():
            return False, '用户参数错误，找不到工单'
        ticket_obj = ticket_queryset.first()
        workflow_queryset = WorkFlow.objects.filter(workflow_ticket=ticket_obj, is_deleted=False)
        if not workflow_queryset:
            return False, '找不到对应的工作流模板，请联系管理员'
        workflow_obj = workflow_queryset.first()
        if not workflow_obj.able_to_add_countersign:
            return False, '当前工作流不允许设置加签，请联系管理员'
        if user_obj.job_id not in ticket_obj.now_handler:
            return False, '只有工单的当前处理人可以使用加签功能'
        temporary_approver_queryset = User.objects.filter(is_deleted=False,
                                                          job_id__in=data.temporary_countersign_jobid_list)
        if len(temporary_approver_queryset) != len(data.temporary_countersign_jobid_list):
            return False, '部分临时审批人工号无效，核实后再提交'
        # ticket_obj = ticket_queryset.first()
        ticket_obj.is_adding_countersign = True
        ticket_obj.temporary_approver = '_' + '_'.join(data.temporary_countersign_jobid_list)
        ticket_obj.save()
        return True, '已设置加签'

    @classmethod
    @log_auto
    def withdraw_ticket(cls, user_obj: User, ticket_id):
        try:
            ticket_obj = Ticket.objects.get(id=ticket_id, is_deleted=False, state='ongoing')
        except ObjectDoesNotExist:
            return False, '用户提交信息有误，找不到对应的工单'
        workflow_obj = WorkFlow.objects.filter(workflow_ticket=ticket_obj, is_deleted=False)
        if not workflow_obj.exists():
            return False, '错误！找不到对应工作流'
        if not workflow_obj.first().able_to_cancel_approve:
            return False, '属于当前工作流的工单不允许撤回'
        if ticket_obj.creator_id != user_obj.id:
            return False, '参数错误，用户只能撤回自己申请的工单'
        ticket_obj.state = 'withdraw'
        history_result_list = ticket_obj.results_of_all_nodes
        updata_data = {
            'job_id': user_obj.job_id,
            'result': 'withdraw',
            'node_order_id': 'withdraw',
        }
        history_result_list.append(updata_data)
        ticket_obj.results_of_all_nodes = history_result_list
        ticket_obj.save()
        return True, '工单已撤回'

    @classmethod
    @log_auto
    def transfer_ticket(cls, user_obj, **kwargs):
        data = TransferTicket(**kwargs)
        try:
            ticket_obj = Ticket.objects.get(id=data.ticket_id, is_deleted=False, state='ongoing')
        except ObjectDoesNotExist:
            return False, '用户提交信息有误，找不到对应的工单'
        workflow_obj = WorkFlow.objects.filter(workflow_ticket=ticket_obj, is_deleted=False)
        if not workflow_obj.exists():
            return False, '错误！找不到对应工作流'
        if not workflow_obj.first().able_to_transfer_approve:
            return False, '属于当前工作流的工单不允许中途移交他人进行审批'
        now_node_approver_jobid_list = (ticket_obj.now_handler[1:]).split('_')
        if not user_obj.job_id in now_node_approver_jobid_list:
            return False, '参数错误，用户只能操作正待自己审批的工单'
        handover_obj = User.objects.filter(job_id=data.handover_jobid, is_deleted=False)
        if not handover_obj.exists():
            return False, '找不到待交接人，检查其工号是否正确'
        now_node_approver_jobid_list.remove(user_obj.job_id)
        now_node_approver_jobid_list.append(data.handover_jobid)
        ticket_obj.now_handler = '_' + '_'.join(now_node_approver_jobid_list)
        ticket_obj.save()
        return True, '已将工单交接'


ticket_ins = TicketSupport()
