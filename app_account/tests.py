from django.test import TestCase
# 账户视图函数的功能测试
# Create your tests here.

import requests, json

class account_test():
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
            # 'csrfmiddlewaretoken': res_get.cookies.get('csrftoken')
                    }
        # headers = {
        #     'Content-Type': 'application/json',
        #     'X-CSRFTOKEN': self._session.cookies.get('csrftoken')
        #             }
        self.set_csrf_hearders()
        res_post = self._session.post(url=url, json=login_data, headers=self.headers)
        return res_post

    def index(self, custom_job_id: str = None):
        res_login = self.login()
        if not custom_job_id:
            custom_job_id = (res_login.json()).get('data').get('job_id')
        url = f'{self.BASE_URL}/app_account/index/{custom_job_id}'
        res_index = self._session.get(url)
        return res_index

    def register(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_account/register/'
        res_get = self._session.get(url)
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def batch_register(self, data_list: list[dict]):
        self.login()
        url = f'{self.BASE_URL}/app_account/register/'
        res_all = {}
        for data in data_list:
            res_get = self._session.get(url)
            self.set_csrf_hearders()
            res_post = self._session.post(url, json=data, headers=self.headers)
            if res_post.status_code != 200:
                res_all['error_data'] = data
                continue
        if not res_all:
            res_all['msg'] = '所有数据均已添加成功'
        else:
            res_all['msg'] = 'error！！部分数据添加不成功'
        return res_all



    def set_pwd(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_account/login/set_pwd/'
        res_get = self._session.get(url)
        # headers = {
        #     'Content-Type': 'application/json',
        #     'X-CSRFTOKEN': self._session.cookies.get('csrftoken')}
        self.set_csrf_hearders()

        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def appoint_workflow_admin(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_account/appoint_workflow_admin/'
        job_id_list: list[str] = [('job_id' + i) for i in data.get('job_id_list', None)]
        url_query_str = '?' + '&'.join(job_id_list)
        query_url = url + url_query_str
        res_get = self._session.get(query_url)
        # headers = {
        #     'Content-Type': 'application/json',
        #     'X-CSRFTOKEN': self._session.cookies.get('csrftoken')}
        self.set_csrf_hearders()

        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def appoint_common(self, **data):
        self.login()
        url = f'{self.BASE_URL}/app_account/appoint_common/'
        job_id_list: list[str] = [('job_id' + i) for i in data.get('job_id_list', None)]
        url_query_str = '?' + '&'.join(job_id_list)
        query_url = url + url_query_str
        res_get = self._session.get(query_url)
        # headers = {
        #     'Content-Type': 'application/json',
        #     'X-CSRFTOKEN': self._session.cookies.get('csrftoken')}
        self.set_csrf_hearders()
        res_post = self._session.post(url, json=data, headers=self.headers)
        return res_post

    def logout(self):
        self.login()
        url = f'{self.BASE_URL}/app_account/logout'
        res_get = self._session.get(url)
        return res_get

    def get_depart(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/'
        query_url = url_base + '?' + 'search_value=' + data['search_value']
        res_get = self._session.get(query_url)
        # self.set_csrf_hearders()
        return res_get

    def add_depart(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/add_depart/'
        res_get = self._session.get(url=url_base)
        self.set_csrf_hearders()
        res_post = self._session.post(url_base, json=data, headers=self.headers)
        return res_post

    def batch_add_depart(self, data: list):
        self.login()
        res_all = {}
        url_base = f'{self.BASE_URL}/app_account/add_depart/'
        for i in data:
            res_get = self._session.get(url=url_base)
            self.set_csrf_hearders()
            res_post = self._session.post(url_base, json=i, headers=self.headers)
            if res_post.status_code != 200:
                res_all['error_data'] = i
                continue
        if not res_all:
            res_all['msg'] = '所有数据均已添加成功'
        else:
            res_all['msg'] = '部分数据出错，未添加成功'
        return res_all


    def depart_edit_patch(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/edit/'
        url_query = url_base + str(data.get('depart_id'))
        res_get = self._session.get(url_query)
        # print(res_get.json())
        self.set_csrf_hearders()
        res_post = self._session.patch(url_query, json=data, headers=self.headers)
        return res_post

    def depart_edit_delete(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/edit/'
        url_query = url_base + str(data.get('depart_id'))
        res_get = self._session.get(url_query)
        # print(res_get.json())
        self.set_csrf_hearders()
        res_delete = self._session.delete(url_query, headers=self.headers)
        return res_delete

    def depart_relation_user_get(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/view/depart{data.get("depart_id")}/relate_user/?per_page={data.get("per_page")}&page={data.get("page")}'
        res_get = self._session.get(url_base)
        return res_get

    def depart_relation_user_post(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/edit/depart{data.get("depart_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_post = self._session.post(url_base, json=data, headers=self.headers)
        return res_post

    def batch_depart_relate_user(self, data:list[dict]):
        self.login()
        res_all = {}
        for i in data:

            url_base = f'{self.BASE_URL}/app_account/depart/edit/depart{i.get("depart_id")}/relate_user/'
            res_get = self._session.get(url_base)
            self.set_csrf_hearders()
            res_post = self._session.post(url_base, json=i, headers=self.headers)
            if res_post.status_code != 200:
                res_all['error_data'] = i
                continue
        if not res_all:
            res_all['msg'] = '所有数据均已添加成功'
        else:
            res_all['msg'] = '部分数据出错，未添加成功'
        return res_all

    def depart_relation_user_patch(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/edit/depart{data.get("depart_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_patch = self._session.patch(url_base, json=data, headers=self.headers)
        return res_patch

    def depart_relation_user_delete(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/depart/edit/depart{data.get("depart_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_delete = self._session.delete(url_base, json=data, headers=self.headers)
        return res_delete
    
    
    
    

    def job_get(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job'
        query_url = url_base + '?' + 'search_value=' + data['search_value']
        res_get = self._session.get(query_url)
        # self.set_csrf_hearders()
        return res_get

    def add_job(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/add_job/'
        res_get = self._session.get(url=url_base)
        self.set_csrf_hearders()
        res_post = self._session.post(url_base, json=data, headers=self.headers)
        return res_post

    def batch_add_job(self, data: list[dict]):
        self.login()
        res_all = {}
        url_base = f'{self.BASE_URL}/app_account/add_job/'
        for i in data:
            res_get = self._session.get(url=url_base)
            self.set_csrf_hearders()
            res_post = self._session.post(url_base, json=i, headers=self.headers)
            if res_post.status_code != 200:
                res_all['error_data'] = i
                continue
        if not res_all:
            res_all['msg'] = '岗位数据全部添加'
        else:
            res_all['msg'] = '有部分数据出错无法添加'
        return res_all

    def job_edit_patch(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/edit/'
        url_query = url_base + str(data.get('jobtitle_id'))
        res_get = self._session.get(url_query)
        # print(res_get.json())
        self.set_csrf_hearders()
        res_post = self._session.patch(url_query, json=data, headers=self.headers)
        return res_post

    def job_edit_delete(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/edit/'
        url_query = url_base + str(data.get('jobtitle_id'))
        res_get = self._session.get(url_query)
        # print(res_get.json())
        self.set_csrf_hearders()
        res_delete = self._session.delete(url_query, headers=self.headers)
        return res_delete

    def job_relation_user_get(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/view/job{data.get("jobtitle_id")}/relate_user/?per_page={data.get("per_page")}&page={data.get("page")}'
        res_get = self._session.get(url_base)
        return res_get

    def job_relation_user_post(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/edit/job{data.get("jobtitle_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_post = self._session.post(url_base, json=data, headers=self.headers)
        return res_post

    def batch_job_relation_user(self, data:list[dict]):
        self.login()
        res_all = {}
        for i in data:
            url_base = f'{self.BASE_URL}/app_account/job/edit/job{i.get("jobtitle_id")}/relate_user/'
            res_get = self._session.get(url_base)
            self.set_csrf_hearders()
            res_post = self._session.post(url_base, json=i, headers=self.headers)
            if res_post.status_code != 200:
                res_all['error_data'] = i
                continue
        if not res_all:
            res_all['msg'] = '所有岗位--用户添加完成'
        else:
            res_all['msg'] = '部分数据出错'
        return res_all




    def job_relation_user_patch(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/edit/job{data.get("jobtitle_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_patch = self._session.patch(url_base, json=data, headers=self.headers)
        return res_patch

    def job_relation_user_delete(self, **data):
        self.login()
        url_base = f'{self.BASE_URL}/app_account/job/edit/job{data.get("jobtitle_id")}/relate_user/'
        res_get = self._session.get(url_base)
        self.set_csrf_hearders()
        res_delete = self._session.delete(url_base, json=data, headers=self.headers)
        return res_delete

    
    
    
    
    
    
    
if __name__ == '__main__':
    user_1 = account_test('001', 'hehe1234') # 超级管理员
    register_data_1 = {
    "name": "susu",
    "password": "susu1234",
    "job_id": "002",
    "email": "susu@qq.com",
    "phone": "18812341234",
    "gender": "female",
    "user_type": "workflow_admin",
    }
    # print(user_1.register(**register_data_1)) # 超级管理员创建用户测试
    # print(user_1.index('001').json()) # 登录后进入index主页的测试
    user_2 = account_test('002', 'susu1234')
    register_data_2 = {
    "name": "lili",
    "password": "lili1234",
    "job_id": "003",
    "email": "susu@qq.com",
    "phone": "18812341234",
    "gender": "female",
    "user_type": "common",
    }
    # print(user_2.register(**register_data_2).json()) # 工作流管理员创建用户测试
    user_3 = account_test('003', 'lili1234')
    register_data_3 = {
    "name": "uiui",
    "password": "uiui1234",
    "job_id": "004",
    "email": "susu@qq.com",
    "phone": "18812341234",
    "gender": "female",
    "user_type": "common",
    }
    # print(user_3.register(**register_data_3).json()) # 普通用户不允许创建新用户测试
    set_pwd_data = {
    'old_pwd': 'lili1234',
    'new_pwd_1': 'lili5678',
    'new_pwd_2': 'lili5678'
    }
    # print(user_3.set_pwd(**set_pwd_data).json()) # 用户修改密码测试
    appoint_workflow_admin_data = {'job_id_list': ['003', '002']}
    # print(user_1.appoint_workflow_admin(**appoint_workflow_admin_data).json()) # 修改用户为工作流管理员功能测试
    appoint_common_data = {'job_id_list': ['003', '002']}
    # print(user_1.appoint_common(**appoint_common_data).json()) # 修改工作流管理员为普通用户
    # print(user_1.logout().json()) # 注销登录测试
    # print(user_2.logout().json())
    depart_data = {
        'name': 'IT部',
        # parent_depart_id: Optional[int]
        # leader_id: Optional[int]
        # approver_id: Optional[int]
    }
    depart_data_2 = {
        'name': '公司',
        'leader_id': 1,
        'approver_id': 1
    }
    depart_data_3 = {
        'name': '前端组',
        'leader_id': 2,
        'approver_id': 2,
        'parent_depart_id': 1
    }
    get_depart_data = {
        'search_value': '公',
        'per_page': 10,
        'page': 1
    }
    # print(user_1.get_depart(**get_depart_data).json()) # 获取部门测试
    # print(user_1.add_depart(**depart_data_3).json()) # 增加部门测试
    depart_edit_patch_data = {
    'depart_id': '1',
    'name': 'IT部',
    'parent_depart_id': 2,
    'leader_id': 3,
    'approver_id': 3
    }
    # print(user_1.depart_edit_patch(**depart_edit_patch_data).json()) # 更新部门测试
    add_depart_data = {
        'name': '测试部'
    }
    delete_depart_data = {
        'depart_id': 4
    }
    # print(user_1.add_depart(**add_depart_data).json())
    # print(user_1.depart_edit_delete(**delete_depart_data).json()) # 删除部门测试

    depart_relation_user_get_data = {
        'depart_id': 3,
        'page': 1,
        'per_page': 10    }
    # print(user_1.depart_relation_user_get(**depart_relation_user_get_data).json())
    depart_relation_user_post_data = {
        'depart_id': 1,
        'job_id': ['002', '003'],

    }
    # print(user_1.depart_relation_user_post(**depart_relation_user_post_data).json())
    # print(user_1.depart_relation_user_get(**depart_relation_user_get_data).json())
    depart_relation_user_patch_data = {
        'depart_id': 1,
        'job_id': ['002', '003'],
        'new_depart_id': 3}
    # print(user_1.depart_relation_user_patch(**depart_relation_user_patch_data).json())
    # print(user_1.depart_relation_user_get(**depart_relation_user_get_data).json())

    depart_relation_user_patch_delete = {
        'depart_id': 3,
        'job_id': ['002']}
    # print(user_1.depart_relation_user_delete(**depart_relation_user_patch_delete).json())
    # print(user_1.depart_relation_user_get(**depart_relation_user_get_data).json())

    job_get_data = {
        'search_value': '前端',
        'per_page': 10,
        'page': 1
    }
    # print(user_1.job_get(**job_get_data).json())
    # 添加岗位
    job_add_data = {
    'name': '前端开发',
    'description': '负责前端页面开发',
    }
    # print(user_1.add_job(**job_add_data).json())
    # 查询岗位
    # print(user_1.job_get(**job_get_data).json())
    job_edit_patch_data = {
    'jobtitle_id': 1,
    'name': '前端开发更新1',
    'description': '前端开发更新描述1'
    }
    # print(user_1.job_edit_patch(**job_edit_patch_data).json()) #更新岗位信息
    # print(user_1.job_get(**job_get_data).json())
    job_edit_delete_data = {
        'jobtitle_id': 1,
    }
    # print(user_1.job_edit_delete(**job_edit_delete_data).json()) # 删除岗位
    # print(user_1.job_get(**job_get_data).json())


    job_add_data_1 = {
    'name': '测试开发',
    'description': '测试开发描述',
    }
    # print(user_1.add_job(**job_add_data_1).json())

    job_add_data_2 = {
    'name': '后端开发',
    'description': '后端开发描述',
    }
    # print(user_1.add_job(**job_add_data_2).json())

    job_relation_user_post_data = {
        'jobtitle_id': 2,
        'job_id': ['002', '003'],
    }
    # print(user_1.job_relation_user_post(**job_relation_user_post_data).json()) # 岗位内添加用户
    job_relation_user_patch_data = {
        'jobtitle_id': 2,
        'job_id': ['003'],
        'new_jobtitle_id': 3
    }
    # print(user_1.job_relation_user_patch(**job_relation_user_patch_data).json()) # 用户在岗位间转移
    job_relation_user_delete_data = {
        'jobtitle_id': 3,
        'job_id': ['003']
    }
    # print(user_1.job_relation_user_delete(**job_relation_user_delete_data).json()) # 岗位内删除用户
    # 获得岗位内的用户
    job_relation_user_get_data = {
        'jobtitle_id': 2,
        'per_page': 10,
        'page': 1,
    }
    # print(user_1.job_relation_user_get(**job_relation_user_get_data).json())

    """以下为准备审批使用的人员、部门、岗位："""
    boss_admin = account_test('001', 'hehe1234')
    user_data_base = {
    # "name": "susu",
    "password": "hehe1234",
    # "job_id": "002",
    "email": "susu@qq.com",
    "phone": "18812341234",
    "gender": "female",
    "user_type": "workflow_admin",
    }
    name_jobid_tuple = [
        ('IT部长er', '002'),
        ('人事部长er', '003'),
        ('开发工程师er', '004'),
        ('开发组长', '005'),
        ('考勤组长er', '006'),
        ('行政部长er', '007'),
        ('行政专员er', '008'),
        ('行政组长er', '009')
    ]
    register_data = []
    for i in name_jobid_tuple:
        cache_dict = user_data_base.copy()
        cache_dict['name'] = i[0]
        cache_dict['job_id'] = i[1]
        register_data.append(cache_dict)

    # print(register_data)
    # print(boss_admin.batch_register(register_data))

    test_depart_data_1 = {
        'name': '公司',
        'leader_id': 1,
        'approver_id': 1,
        # 'parent_depart_id': 1
    }
    test_depart_data_2 = {
        'name': 'IT部',
        'leader_id': 2,
        'approver_id': 2,
        'parent_depart_id': 1
    }
    test_depart_data_3 = {
        'name': '开发组',
        'leader_id': 5,
        'approver_id': 5,
        'parent_depart_id': 2
    }
    test_depart_data_4 = {
        'name': '人事部',
        'leader_id': 3,
        'approver_id': 3,
        'parent_depart_id': 1
    }
    test_depart_data_5 = {
        'name': '考勤组',
        'leader_id': 6,
        'approver_id': 6,
        'parent_depart_id': 4
    }
    test_depart_data_6 = {
        'name': '行政部',
        'leader_id': 7,
        'approver_id': 7,
        'parent_depart_id': 1
    }
    test_depart_data_7 = {
        'name': '行政组',
        'leader_id': 9,
        'approver_id': 9,
        'parent_depart_id': 6
    }
    # print(dir(globals()))
    # print(globals().get('test_depart_data_7'))
    # add_depart_list = [
    #     globals()[i] for i in globals().keys() if i.startswith('test_depart_data_')
    # ]
    # for i in add_depart_list:
    #     print(i)
    # print(boss_admin.batch_add_depart(add_depart_list))

    test_job_add_data = {
    'name': '开发工程师',
    'description': '描述',
    }
    job_name_list = [
        '开发工程师',
        'IT部长',
        '人事部长',
        '考勤组长',
        '行政部长',
        '行政专员',
        '行政组长',
        '公司老板'
    ]
    test_jobtitle_list = []
    for i in job_name_list:
        dd = dict(name=i, description=i+'描述')
        test_jobtitle_list.append(dd)
    # print(test_jobtitle_list)
    # print(boss_admin.batch_add_job(test_jobtitle_list))

    job_relation_user_data = []
    job_relate_user_data = [
        (2, ['002']),
        (3, ['003']),
        (1, ['004', '005']),
        (4, ['006']),
        (5, ['007']),
        (6, ['008']),
        (7, ['009']),
        (8, ['001']),
    ]
    for i in job_relate_user_data:
        dd = {
            'jobtitle_id': i[0],
            'job_id': i[1],
        }
        job_relation_user_data.append(dd)
    # print(job_relation_user_data)
    # print(boss_admin.batch_job_relation_user(job_relation_user_data))

    depart_relate_user_data = {
        'depart_id': 1,
        'job_id': ['002', '003'],

    }
    depart_user_tuple_data = [
        (1, ['001']),
        (2, ['002']),
        (4, ['003']),
        (3, ['004', '005']),
        (5, ['006']),
        (6, ['007']),
        (7, ['008', '009'])
    ]
    test_depart_user_list = []
    for i in depart_user_tuple_data:
        dd = dict(depart_id=i[0], job_id=i[1])
        test_depart_user_list.append(dd)
    # print(boss_admin.batch_depart_relate_user(test_depart_user_list))


