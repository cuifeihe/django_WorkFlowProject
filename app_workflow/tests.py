from django.test import TestCase
# workflow视图函数的功能测试
# Create your tests here.


import requests, json

class workflow_test():
    BASE_URL = 'http://localhost:8000'

    def __init__(self, username, pwd):
        self.username = username
        self.pwd = pwd
        self._session = requests.Session()

    def set_csrf_hearders(self):
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFTOKEN': self._session.cookies.get('csrftoken')}
        self.headers = headers

    def login(self):
        url = f'{self.BASE_URL}/app_account/login/'
        res_get = self._session.get(url=url)
        login_data = {
            'job_id': self.username,
            'password': self.pwd,
                }
        self.set_csrf_hearders()
        res_post = self._session.post(url=url, json=login_data, headers=self.headers)
        return res_post

    def index(self, **data):
        res_login = self.login()
        url = f'{self.BASE_URL}/app_workflow/index'
        if data.get('search_value'):
            url += f"?search_value={data.get('search_value')}"
        if data.get('per_page'):
            url += f"&per_page={data.get('per_page')}"
        if data.get('page'):
            url += f"&page={data.get('page')}"

        res_get = self._session.get(url)
        return res_get

    def workflow_get_detail(self, workflow_id):
        res_login = self.login()
        url = f'{self.BASE_URL}/app_workflow/workflow{workflow_id}/get_detail/'
        res_get = self._session.get(url)
        return res_get

    def add_workflow(self, **data):
        res_login = self.login()
        url = f'{self.BASE_URL}/app_workflow/add/'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def edit_workflow_post(self, **data):
        res_login = self.login()
        url = f'{self.BASE_URL}/app_workflow/workflow{data.get("workflow_id")}/edit/'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def edit_workflow_switch(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_workflow/workflow{data.get("workflow_id")}/function_switch/'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

if __name__ == '__main__':
    admin_user = workflow_test('001', 'hehe1234')
    workflow_user_1 = workflow_test('002', 'hehe1234')
    index_data_admin = {
        'search_value': '年假',
        'per_page': 10,
        'page': 1,
    }
    # print(admin_user.index(**index_data_admin).json())
    workflow_id_1 = 1
    # print(admin_user.workflow_get_detail(workflow_id_1).json())
    # print(workflow_user_1.workflow_get_detail(workflow_id_1).json())

    add_workflow_data_1 = {
        'name': '年假申请审批测试',
        'description': '年假申请审批测试描述'
        # creator: int
        # able_to_cancel_approve: Optional[bool]
        # able_to_add_countersign: Optional[bool]
        # able_to_transfer_approve: Optional[bool]
        # view_permission_check: Optional[bool]
        # submit_ticket_check: Optional[bool]
        # limit_expression: Optional[WorkflowLimitExpression]
    }
    # print(admin_user.add_workflow(**add_workflow_data_1).json())
    #
    node_data_1 = {
        'name': '开始',
        # 'id': int,
        'node_type': 'begin',
        'participant_type': 'other',
        # 'participant': NodeParticipant,
        'order_id': 1,
    }
    node_data_2 = {
        'name': '组长审批的节点',
        # 'id': int,
        'node_type': 'serial',
        'participant_type': 'depart',
        'participant': {'depart':3},
        'order_id': 2,
    }
    node_data_3 = {
        'name': '请假天数的条件节点',
        # 'id': int,
        'node_type': 'condition',
        'participant_type': 'other',
        # 'participant': NodeParticipant,
        'order_id': 3,
    }
    node_data_4 = {
        'name': '小于5天的并行会签',
        # 'id': int,
        'node_type': 'parallel_all',
        'participant_type': 'multi_person',
        'participant': {"multi_person": ['002', '008']},
        'order_id': 4,
    }
    node_data_5 = {
        'name': '大于10天的老板角色',
        # 'id': int,
        'node_type': 'serial',
        'participant_type': 'depart',
        'participant': {'depart':1},
        'order_id': 5,
    }
    node_data_6 = {
        'name': '5到10内的IT部长角色',
        # 'id': int,
        'node_type': 'serial',
        'participant_type': 'depart',
        'participant': {'depart':2},
        'order_id': 6,
    }
    node_data_7 = {
        'name': '5到10内的并行或签',
        # 'id': int,
        'node_type': 'parallel_any',
        'participant_type': 'multi_person',
        'participant': {"multi_person": ['003', '006']},
        'order_id': 7,
    }
    node_data_8 = {
        'name': '结束',
        # 'id': int,
        'node_type': 'end',
        'participant_type': 'other',
        # 'participant': NodeParticipant,
        'order_id': 8,
    }
    node_list = [
        globals().get(i) for i in globals() if i.startswith('node_data_')
    ]

    node_relation_data_1 = {
        'name': '开始提交至组长',
        'source_node_id': 1,
        'destination_node_id': 2,
        'relation': 'agree',
    }
    node_relation_data_2 = {
        'name': '组长审批通过',
        'source_node_id': 2,
        'destination_node_id': 3,
        'relation': 'agree',
    }
    node_relation_data_3 = {
        'name': '年假天数条件小于5',
        'source_node_id': 3,
        'destination_node_id': 4,
        'relation': 'count_compare_condition_result'
    }
    node_relation_data_4 = {
        'name': '年假天数条件大于10',
        'source_node_id': 3,
        'destination_node_id': 5,
        'relation': 'count_compare_condition_result',
    }
    node_relation_data_5 = {
        'name': '年假天数条件5到10之间',
        'source_node_id': 3,
        'destination_node_id': 6,
        'relation':  'count_compare_condition_result',
    }
    node_relation_data_6 = {
        'name': '并行会签通过审批',
        'source_node_id': 4,
        'destination_node_id': 8,
        'relation': 'agree',
    }
    node_relation_data_7 = {
        'name': '老板通过',
        'source_node_id': 5,
        'destination_node_id': 8,
        'relation': 'agree',
    }
    node_relation_data_8 = {
        'name': 'IT部长通过',
        'source_node_id': 6,
        'destination_node_id': 7,
        'relation': 'agree',
    }
    node_relation_data_9 = {
        'name': '并行或签通过',
        'source_node_id': 7,
        'destination_node_id': 8,
        'relation': 'agree',
    }
    node_relation_list = [
        globals().get(i) for i in globals() if i.startswith('node_relation_data_')
    ]

    custom_field_data_1 = {
        'field_name': '申请的年假天数',
        'description': '根据用户提交的请假天数，动态决定审批的方向',
        'field_type': 'count_compare',
        'field_in_node': 3,   # 应该是本工作流的order_id
        'critical_value': {'critical_value': [5, 10]}
    }
    condition_result_data_1 = {
        # 'node_relation_id': 3,
        'node_relation_name': '年假天数条件小于5',
        'field_type': 'count_compare',
        'condition_result_count_compare': {
            'low_bound': 0,
            'low_bound_is_close': False,
            'up_bound': 5,
            'up_bound_is_close': False,
        }
        # 'condition_result_right_or_wrong': Optional[BranchOfRightOrWrong]
    }
    condition_result_data_2 = {
        # 'node_relation_id': 4,
        'node_relation_name': '年假天数条件大于10',
        'field_type': 'count_compare',
        'condition_result_count_compare': {
            'low_bound': 10,
            'low_bound_is_close': False,
            # 'up_bound': 5,
            # 'up_bound_is_close': False,
        }
    }
    condition_result_data_3 = {
        # 'node_relation_id': 5,
        'node_relation_name': '年假天数条件5到10之间',
        'field_type': 'count_compare',
        'condition_result_count_compare': {
            'low_bound': 5,
            'low_bound_is_close': True,
            'up_bound': 10,
            'up_bound_is_close': True,
        }
    }
    condition_result_list = [
        globals().get(i) for i in globals() if i.startswith('condition_result_data_')
    ]


    edit_workflow_post_data = {
        'workflow_id': 1,
        'node': node_list,
        'node_relation': node_relation_list,
        'custom_field': [custom_field_data_1],
        'condition_result': condition_result_list,
    }
    # print(admin_user.edit_workflow_post(**edit_workflow_post_data).json())

    # def print_list_data(data: list):
    #     for i in data:
    #         print(i)
    # print_list_data(node_list)
    # print_list_data(node_relation_list)
    # print_list_data(condition_result_list)

    # 测试工作流功能开关
    edit_workflow_switch_data_1 = {
        'workflow_id': 1,
        # creator: int
        'able_to_cancel_approve': False,
        'able_to_add_countersign': False,
        'able_to_transfer_approve': False,
        # view_permission_check: bool

        'submit_ticket_check': True,
        'limit_expression': {
            'limit_method': {
                # 'limit_type': str = 'limit_count_and_period'
                'period': 2,  # 限制周期({"period":24} 24小时),
                'count': 1  # 限制次数({"count":1}在限制周期内只允许提交1次),
            }
        }
    }
    # print(workflow_user_1.edit_workflow_switch(**edit_workflow_switch_data_1).json())
    edit_workflow_switch_data_2 = {
        'workflow_id': 1,
        # creator: int
        'able_to_cancel_approve': False,
        'able_to_add_countersign': False,
        'able_to_transfer_approve': False,
        # view_permission_check: bool

        'submit_ticket_check': True,
        'limit_expression': {
            'limit_method': {
                # 'limit_type': str = 'limit_count_and_period'
                # 'period': 2,  # 限制周期({"period":24} 24小时),
                # 'count': 1  # 限制次数({"count":1}在限制周期内只允许提交1次),
                'allow_type': 'jobid',  # , 'depart', 'jobtitle']
                'allow_jobid': ['004', '005']  # 只允许特定人员提交
                # 'allow_depart_id': Optional[List[int]]  # 只允许特定部门提交
                # 'allow_jobtitle_id': Optional[List[int]]  # 只允许特定岗位提交
            }
        }
    }
    # print(workflow_user_1.edit_workflow_switch(**edit_workflow_switch_data_2).json())

    edit_workflow_switch_data_3 = {
        'workflow_id': 1,
        # creator: int
        'able_to_cancel_approve': False,
        'able_to_add_countersign': False,
        'able_to_transfer_approve': False,
        # view_permission_check: bool

        'submit_ticket_check': True,
        'limit_expression': {
            'limit_method': {
                # 'limit_type': str = 'limit_count_and_period'
                # 'period': 2,  # 限制周期({"period":24} 24小时),
                # 'count': 1  # 限制次数({"count":1}在限制周期内只允许提交1次),
                'allow_type': 'jobtitle',  # , '', '']jobiddepart
                # 'allow_jobid': ['004', '005']  # 只允许特定人员提交
                # 'allow_depart_id': [2, 3]  # 只允许特定部门提交
                'allow_jobtitle_id': [1, 7]  # 只允许特定岗位提交
            }
        }
    }
    # print(workflow_user_1.edit_workflow_switch(**edit_workflow_switch_data_3).json())