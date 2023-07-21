import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from common.decorators import log_auto
from app_workflow.models import WorkFlow, Node, NodeRelation, CustomField, ConditionResult
from interface.workflow_view_interface import GetAllWorkflowInfo, AddWorkflow, AddWorkflowDetail, \
    SetWorkflowFunctionSwitch
from app_account.models import User, Depart

class WorkflowSupport(object):
    """工作流相关的服务，供视图调用"""
    @classmethod
    @log_auto
    def get_all_workflow_info(cls, **kwargs):
        """获得所有的工作流信息"""
        data = GetAllWorkflowInfo(**kwargs)
        search_expression = Q(is_deleted=False)
        if data.search_value:
            search_expression &= Q(name__icontains=data.search_value)
        if data.user_type == 'workflow_admin':
            search_expression &= Q(creator_id=data.user_id)
        workflow_queryset = WorkFlow.objects.filter(search_expression)
        if not workflow_queryset:
            return False, '找不到工作流'
        paginator = Paginator(workflow_queryset, data.per_page)
        try:
            target_page_result = paginator.page(data.page)
        except PageNotAnInteger:
            target_page_result = paginator.page(1)
        except EmptyPage:
            target_page_result = paginator.page(paginator.num_pages)
        target_page_obj_list = target_page_result.object_list
        workflow_info_result_list = []
        for i in target_page_obj_list:
            workflow_info_result_list.append(i.info)
        return True, dict(workflow_info=workflow_info_result_list,
                          per_page=data.per_page, page=data.page, total_obj=paginator.count)

    @classmethod
    @log_auto
    def add_workflow(cls, **kwargs):
        data = AddWorkflow(**kwargs)
        if WorkFlow.objects.filter(name=data.name, is_deleted=False).exists():
            return False, "该名称的工作流已存在"
        workflow_obj = WorkFlow(name=data.name, description=data.description,
                                able_to_cancel_approve=data.able_to_cancel_approve,
                                able_to_add_countersign=data.able_to_add_countersign,
                                able_to_transfer_approve=data.able_to_transfer_approve,
                                view_permission_check=data.view_permission_check,
                                submit_ticket_check=data.submit_ticket_check,
                                creator_id=data.creator)
        if data.limit_expression:
            workflow_obj.limit_expression = data.limit_expression.json()

        workflow_obj.save()
        return True, dict(workflow_id=workflow_obj.id)

    @classmethod
    @log_auto
    def get_workflow_detail(cls, workflow_id):
        """
        获取某工作流详细信息（节点、节点关系、自定义字段分支、）
        :param kwargs:
        :return:
        """
        try:
            workflow_id = int(workflow_id)
            workflow_obj = WorkFlow.objects.get(id=workflow_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, "请求的工作流不存在"
        node_queryset = workflow_obj.workflow_node.filter(is_deleted=False)
        node_list = []
        for node in node_queryset:
            node_list.append(node.info)

        node_relation_queryset = workflow_obj.workflow_node_relation.filter(is_deleted=False)
        node_relation_list = []
        for relation in node_relation_queryset:
            node_relation_list.append(relation.info)

        customfield_queryset = workflow_obj.workflow_custom_field.filter(is_deleted=False)
        if customfield_queryset.exists():
            # customfield_queryset = workflow_obj.workflow_custom_field.all()
            customfield_result_queryset = workflow_obj.workflow_conditionresult.filter(is_deleted=False)
            customfield_list = []
            for field in customfield_queryset:
                customfield_list.append(field.info)

            customfield_result_list = []
            for result in customfield_result_queryset:
                customfield_result_list.append(result.info)

            workflow_detail = {
                'node_list': node_list, 'node_relation_list': node_relation_list,
                'customfield_list': customfield_list, 'customfield_result_list': customfield_result_list}
            return True, workflow_detail

        workflow_detail = {
            'node_list': node_list, 'node_relation_list': node_relation_list}
        return True, workflow_detail


    @classmethod
    @log_auto
    def add_workflow_detail(cls, **kwargs):
        """配置一个工作流（包括其节点、节点关系、自定义字段、自定义字段结果）"""
        data = AddWorkflowDetail(**kwargs)
        try:
            workflow_obj = WorkFlow.objects.get(id=data.workflow_id, is_deleted=False)
        except ObjectDoesNotExist:
            return False, "请求的工作流不存在"

        # node_obj_list = [] # 配置节点
        for n in data.node:
            node_obj = Node(workflow=workflow_obj, name=n.name, node_type=n.node_type, participant_type=n.participant_type,
                            creator_id=data.creator, order_id=n.order_id)
            node_obj.save()
            if n.participant_type == 'one_person':
                node_obj.participant_one_person_id = n.participant.one_person
                node_obj.save()

            elif n.participant_type == 'multi_person':
                multi_person_queryset = User.objects.filter(job_id__in=n.participant.multi_person, is_deleted=False)
                node_obj.participant_multi_person.add(*multi_person_queryset)

            elif n.participant_type == 'depart':
                depart_obj = Depart.objects.get(id=n.participant.depart, is_deleted=False)
                node_obj.participant_depart_id = depart_obj.id
                node_obj.save()
            elif n.participant_type == 'role':
                node_obj.participant_role = n.participant.role.json()
                node_obj.save()
            elif n.participant_type == 'other':
                pass

        #     node_obj_list.append(node_obj)
        # Node.objects.bulk_create(node_obj_list)

        node_relation_obj_list = [] # 配置节点关系
        for nr in data.node_relation:
            # 先从workflow和order_id获得节点id用作外键关联
            source_node_obj = Node.objects.get(workflow_id=workflow_obj.id, is_deleted=False, order_id=nr.source_node_id)
            destination_node_obj = Node.objects.get(workflow_id=workflow_obj.id, is_deleted=False, order_id=nr.destination_node_id)
            node_relation_obj = NodeRelation(name=nr.name, workflow=workflow_obj,
                                             source_node_id=source_node_obj.id,
                                             destination_node_id=destination_node_obj.id,
                                             relation=nr.relation, creator_id=data.creator)
            node_relation_obj_list.append(node_relation_obj)

        NodeRelation.objects.bulk_create(node_relation_obj_list)

        if not data.custom_field:
            return True, '工作流节点内容已添加完成'

        else:
            custom_field_obj_list = [] # 配置自定义字段

            for c in data.custom_field:
                target_node_obj = Node.objects.get(workflow=workflow_obj, is_deleted=False, order_id=c.field_in_node) # 获得自定义字段所在的节点
                if c.field_type == 'count_compare':
                    custom_field_obj = CustomField(workflow=workflow_obj, field_name=c.field_name,
                                                   description=c.description, field_type=c.field_type,
                                                   field_in_node_id=target_node_obj.id,
                                                   critical_value_list=c.critical_value.json(), # json格式、数据结构
                                                   creator_id=data.creator)
                    custom_field_obj_list.append(custom_field_obj)

                elif c.field_type == 'right_or_wrong':
                    custom_field_obj = CustomField(workflow=workflow_obj, field_name=c.field_name,
                                                   description=c.description, field_type=c.field_type,
                                                   field_in_node_id=target_node_obj.id,
                                                   compare_constant=c.critical_value.json(), # json格式、数据结构
                                                   creator_id=data.creator)
                    custom_field_obj_list.append(custom_field_obj)
                else:
                    pass
            CustomField.objects.bulk_create(custom_field_obj_list)

            condition_result_obj_list = [] # 配置自定义字段的结果
            for condition_result_data in data.condition_result:
                # 获得分支对应的节点关系
                customfield_node_relation_target_obj = NodeRelation.objects.get(workflow=workflow_obj, is_deleted=False, name=condition_result_data.node_relation_name)
                if condition_result_data.field_type == 'count_compare':
                    condition_result_obj = ConditionResult(workflow=workflow_obj,
                                                           noderelation_id=customfield_node_relation_target_obj.id, #
                                                       low_bound=condition_result_data.condition_result_count_compare.low_bound,
                                                        low_bound_is_close=condition_result_data.condition_result_count_compare.low_bound_is_close,
                                                        up_bound=condition_result_data.condition_result_count_compare.up_bound,
                                                        up_bound_is_close=condition_result_data.condition_result_count_compare.up_bound_is_close,
                                                        creator_id=data.creator)
                    condition_result_obj_list.append(condition_result_obj)

                elif condition_result_data.field_type == 'right_or_wrong':
                    condition_result_obj = ConditionResult(workflow=workflow_obj,
                                                           noderelation_id=customfield_node_relation_target_obj.id,
                                                           condition_is_satisfied=condition_result_data.condition_result_right_or_wrong.condition_is_satisfied,
                                                           condition_not_satisfied=condition_result_data.condition_result_right_or_wrong.condition_not_satisfied,
                                                           creator_id=data.creator)
                    condition_result_obj_list.append(condition_result_obj)
                else:
                    pass
            ConditionResult.objects.bulk_create(condition_result_obj_list)

        return True, '工作流节点内容已添加完成'

    @classmethod
    @log_auto
    def delete_workflow(cls, workflow_id, user_obj):
        """删除某工作流（同时删除 对应的节点、节点关系、自定义字段、自定义字段判断条件的结果、"""
        try:
            workflow_obj = WorkFlow.objects.get(is_deleted=False, id=workflow_id)
        except ObjectDoesNotExist:
            return False, "请求的工作流不存在或者已删除"
        if user_obj.user_type != 'super_admin':
            if workflow_obj.creator.id != user_obj.id:
                return False, '您只能删除您自己创建的工作流'
        node_queryset = Node.objects.filter(workflow=workflow_obj, is_deleted=False)
        node_relation_queryset = NodeRelation.objects.filter(workflow=workflow_obj, is_deleted=False)
        customfield_queryset = CustomField.objects.filter(workflow=workflow_obj, is_deleted=False)
        conditionresult_queryset = ConditionResult.objects.filter(workflow=workflow_obj, is_deleted=False)
        if customfield_queryset:
            for i in customfield_queryset:
                i.is_deleted = True
            CustomField.objects.bulk_update(customfield_queryset, ['is_deleted'])
        if conditionresult_queryset:
            for i in conditionresult_queryset:
                i.is_deleted = True
            ConditionResult.objects.bulk_update(conditionresult_queryset, ['is_deleted'])
        for i in node_relation_queryset:
            i.is_deleted = True
            NodeRelation.objects.bulk_update(node_relation_queryset, ['is_deleted'])
        for i in node_queryset:
            i.is_deleted = True
            Node.objects.bulk_update(node_queryset, ['is_deleted'])
        return True, '工作流删除成功，对应节点、节点关系等一并删除成功'

    @classmethod
    @log_auto
    def set_workflow_function_switch(cls, user_obj:User, **kwargs):
        """配置已有工作流的功能开关（是否允许中途撤回审批、是否允许中途加签、是否允许中途移交他人审批、是否限制工单查看、是否限制工单的提交申请及何种限制方式）"""
        # 还要记得再ticket相关函数前面加上开关检查的if
        data = SetWorkflowFunctionSwitch(**kwargs)
        workflow_queryset = WorkFlow.objects.filter(id=data.workflow_id, is_deleted=False)
        if not workflow_queryset.exists():
            return False, 'url参数错误'
        workflow_obj = workflow_queryset.first()

        workflow_obj.able_to_cancel_approve = data.able_to_cancel_approve
        workflow_obj.able_to_add_countersign = data.able_to_add_countersign
        workflow_obj.able_to_transfer_approve = data.able_to_transfer_approve

        # workflow_obj.view_permission_check = data.view_permission_check

        workflow_obj.submit_ticket_check = data.submit_ticket_check
        if data.submit_ticket_check:
            if not data.limit_expression:
                return False, '当限制工单的提交申请为True时，限制工单提交的策略表达式必须提供'
            workflow_obj.limit_expression = data.limit_expression.json()

        workflow_obj.save()
        return True, '该工作流的功能开关已配置完成'


workflow_ins = WorkflowSupport()