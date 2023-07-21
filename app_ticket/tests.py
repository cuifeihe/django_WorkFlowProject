import requests
from django.test import TestCase
# 工单相关功能测试
# Create your tests here.

class ticket_test():
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

    def submit_ticket(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/submit_ticket/'
        res_get = self._session.get(url=url)
        self.set_csrf_hearders()
        res_post = self._session.post(url=url, json=data, headers=self.headers)
        return res_post

    def workflow_index(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/index?'
        for k, v in data.items():
            url += f'{k}={v}&'
        res_get = self._session.get(url=url[:-1])
        # print(url[:-1])
        return res_get

    def approve_ticket_get(self): # 需要测试不同人员登录时获得的工单
        self.login()
        url = f'{self.BASE_URL}/app_ticket/approve_ticket_get'
        res_get = self._session.get(url=url)
        return res_get

    def approve_ticket(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/approve/ticket{data.get("ticket_id")}'
        res_get = self._session.get(url=url)
        self.set_csrf_hearders()
        res_post = self._session.post(url=url, json=data, headers=self.headers)
        return res_post

    def user_index(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/user_index?type={data.get("type")}&page={data.get("page", 1)}&per_page={data.get("per_page", 10)}'
        res_get = self._session.get(url)
        return res_get

    def add_countersign(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/add_countersign/ticket{data.get("ticket_id")}'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def withdraw_ticket(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/withdraw_ticket/ticket{data.get("ticket_id")}'
        res_get = self._session.get(url=url)
        return res_get

    def transfer_ticket(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_ticket/transfer_ticket/ticket{data.get("ticket_id")}'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post


if __name__ == '__main__':
    admin_user_001 = ticket_test('001', 'hehe1234') # 老板
    workflow_user_IT_leader_002 = ticket_test('002', 'hehe1234') # IT部长
    workflow_user_personnel_leader_003 = ticket_test('003', 'hehe1234') # 人事部长
    common_user_developer_004 = ticket_test('004', 'hehe1234') # 开发工程师
    common_user_developer_team_leader_005 = ticket_test('005', 'hehe1234') # 开发组长
    common_user_attendance_team_leader_006 = ticket_test('006', 'hehe1234') # 考勤组长
    workflow_user_adminis_leader_007 = ticket_test('007', 'hehe1234') # 行政部长
    common_user_adminis_er_008 = ticket_test('008', 'hehe1234') # 行政专员
    common_user_admins_team_leader_009 = ticket_test('009', 'hehe1234') # 行政组长

    submit_data_1 = {
        'title': '004开发工程师提交请年假申请',
        # apply_user: int
        'workflow_id': 1,
        'data': {
            # apply_person_jobid: int
            # workflow_id: int
            'workflow_name': '年假申请审批测试',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假7天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 7,
            }]
        }
        # creator: int
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_1).json()) # 测试工单提交
    index_data = {
        'state': 'ongoing',
        'apply_user_jobid': '004',
        'search_value': '假',
    }
    # print(workflow_user_1.workflow_index(**index_data).json())

    # print(admin_user_001.approve_ticket_get().json())
    # print(workflow_user_IT_leader_002.approve_ticket_get().json()) # 002
    # #
    # print(workflow_user_personnel_leader_003.approve_ticket_get().json())
    # print(common_user_developer_004.approve_ticket_get().json())
    # print(common_user_developer_team_leader_005.approve_ticket_get().json()) # 005
    #
    # print(common_user_attendance_team_leader_006.approve_ticket_get().json())
    # print(workflow_user_adminis_leader_007.approve_ticket_get().json())
    # print(common_user_adminis_er_008.approve_ticket_get().json())
    # print(common_user_admins_team_leader_009.approve_ticket_get().json())



    approve_data_005 = {
        # 'user_id': int,
        'ticket_id': 15,
        'suggestion': '我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005).json())

    approve_data_002 = {
        'ticket_id': 15,
        'suggestion': '我是IT部长，我审批通过',
        'approveresult': 'agree',
    }
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002).json())

    approve_data_003_6 = {
        'ticket_id': 15,
        'suggestion': '我是人事部长、考勤组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_attendance_team_leader_006.approve_ticket(**approve_data_003_6).json())

    # 第二次测试审批
    submit_data_2 = {
        'title': '004开发工程师提交请年假申请--2',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试2',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假18天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 18,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_2).json())
    approve_data_005_2 = {
        # 'user_id': int,
        'ticket_id': 18,
        'suggestion': '第二次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_2).json())
    approve_data_001 = {
        'ticket_id': 18,
        'suggestion': '我是老板，我审批通过',
        'approveresult': 'agree',
    }
    # print(admin_user_001.approve_ticket(**approve_data_001).json())
    # 第三次测试审批
    submit_data_3 = {
        'title': '004开发工程师提交请年假申请--3',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试3',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假3天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 3,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_3).json())
    approve_data_005_3 = {
        # 'user_id': int,
        'ticket_id': 20,
        'suggestion': '第三次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_3).json())
    approve_data_002_008 = {
        'ticket_id': 20,
        'suggestion': '我是IT部长、行政专员，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_adminis_er_008.approve_ticket(**approve_data_002_008).json())
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002_008).json())

    # 第四次、测试拒绝
    submit_data_4 = {
        'title': '004开发工程师提交请年假申请--4',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试4',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假5天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 5,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_4).json())
    approve_data_005_4 = {
        # 'user_id': int,
        'ticket_id': 21,
        'suggestion': '第四次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_4).json())
    approve_data_002_reject = {
        'ticket_id': 21,
        'suggestion': '我是IT部长，我审批拒绝',
        'approveresult': 'reject',
    }
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002_reject).json())

    # 代码优化之后的测试
    submit_data_5 = {
        'title': '004开发工程师提交请年假申请--5',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试4',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假10天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 10,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_5).json())
    approve_data_005_5 = {
        # 'user_id': int,
        'ticket_id': 23,
        'suggestion': '第5次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_5).json())
    approve_data_002_5 = {
        'ticket_id': 23,
        'suggestion': '第五次测试，我是IT部长，我审批通过',
        'approveresult': 'agree',
    }
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002_5).json())
    approve_data_003_006_5 = {
        'ticket_id': 23,
        'suggestion': '我是人事部长、考勤组长，我审批不通过',
        # 'approveresult': 'agree',
        'approveresult': 'reject',
    }
    # print(common_user_attendance_team_leader_006.approve_ticket(**approve_data_003_006_5).json())

    user_index_data = {
        # "type": 'my_submit',
        "type": 'my_approve',
        "page": 1,
        "per_page": 10

    }
    # res_user_index = common_user_developer_004.user_index(**user_index_data).json()
    # print(res_user_index)
    # print(res_user_index['data'])
    # print(workflow_user_IT_leader_002.user_index(**user_index_data).json())

    # 测试中途加签
    submit_data_6 = {
        'title': '004开发工程师提交请年假申请--6',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试4',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假8天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 8,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_6).json())
    approve_data_005_6 = {
        # 'user_id': int,
        'ticket_id': 24,
        'suggestion': '第四次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_6).json())
    add_countersign_data = {
        'ticket_id': 24,
        'temporary_countersign_jobid_list': ['007']
    }
    # print(workflow_user_IT_leader_002.add_countersign(**add_countersign_data).json())
    approve_data_007_6 = {
        # 'user_id': int,
        'ticket_id': 24,
        'suggestion': '第四次测试审批；我是人事部长来临时加签审批，我审批通过',
        'approveresult': 'agree',
    }
    # print(workflow_user_adminis_leader_007.approve_ticket(**approve_data_007_6).json())
    approve_data_002_6 = {
        'ticket_id': 24,
        'suggestion': '第6次测试，我是IT部长，我审批通过',
        'approveresult': 'agree',
    }
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002_6).json())
    approve_data_007_6_reject = {
        # 'user_id': int,
        'ticket_id': 24,
        'suggestion': '第四次测试审批；我是人事部长来临时加签审批，我审批拒绝',
        'approveresult': 'reject',
    }
    # print(workflow_user_adminis_leader_007.approve_ticket(**approve_data_007_6_reject).json())

    add_countersign_data_2 = {
        'ticket_id': 24,
        'temporary_countersign_jobid_list': ['007']
    }
    # print(workflow_user_personnel_leader_003.add_countersign(**add_countersign_data_2).json())

    # 测试工单撤销
    submit_data_7 = {
        'title': '004开发工程师提交请年假申请--7',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试7',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假3天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 3,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_7).json())
    withdraw_data = {
        'ticket_id': 25
    }
    withdraw_data_2 = {
        'ticket_id': 21
    }

    # print(workflow_user_adminis_leader_007.withdraw_ticket(**withdraw_data).json())
    # print(common_user_developer_004.withdraw_ticket(**withdraw_data_2).json())
    # print(common_user_developer_004.withdraw_ticket(**withdraw_data).json())

    # 测试转交工单审批
    submit_data_8 = {
        'title': '004开发工程师提交请年假申请--8',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试8',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假5天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 5,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_8).json())
    transfer_data_1 = {
        'ticket_id': 26,
        'handover_jobid': '006'
    }
    # print(common_user_developer_team_leader_005.transfer_ticket(**transfer_data_1).json())
    approve_data_006_6 = {
        # 'user_id': int,
        'ticket_id': 26,
        'suggestion': '第四次测试审批；我是考勤组长来临时加签审批，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_attendance_team_leader_006.approve_ticket(**approve_data_006_6).json())

    submit_data_9 = {
        'title': '004开发工程师提交请年假申请--9',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试8',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假9天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 9,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_9).json())
    submit_data_10 = {
        'title': '004开发工程师提交请年假申请--10',
        'workflow_id': 1,
        'data': {
            'workflow_name': '年假申请审批测试8',
            'apply_cause': '申请原因：工号004员工开发工程师申请年假10天',
            'custom_field': [{
                'customfield_key': 'custom_field_3',
                'customfield_value': 10,
            }]
        }
    }
    # print(common_user_developer_004.submit_ticket(**submit_data_10).json())
    # print(common_user_admins_team_leader_009.submit_ticket(**submit_data_10).json())
    # print(workflow_user_adminis_leader_007.submit_ticket(**submit_data_10).json())

    approve_data_005_27 = {
        # 'user_id': int,
        'ticket_id': 27,
        'suggestion': '第四次测试审批；我是开发组长，我审批通过',
        'approveresult': 'agree',
    }
    # print(common_user_developer_team_leader_005.approve_ticket(**approve_data_005_27).json())

    approve_data_002_27 = {
        'ticket_id': 27,
        'suggestion': '第6次测试，我是IT部长，我审批通过',
        'approveresult': 'agree',
    }
    # print(workflow_user_IT_leader_002.approve_ticket(**approve_data_002_27).json())

    approve_data_003_27 = {
        'ticket_id': 24,
        'suggestion': '第6次测试，我是003，我审批通过',
        'approveresult': 'agree',
    }
    print(workflow_user_IT_leader_002.approve_ticket(**approve_data_003_27).json())