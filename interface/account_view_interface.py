"""账户相关的接口"""

from pydantic import BaseModel
from typing import Literal, Optional, List


class LoginData(BaseModel):
    """用户登录接口"""
    job_id: str
    password: str

class AddUser(BaseModel):
    """增加用户"""
    name: str
    password: str
    job_id: str
    email: str
    phone: str
    gender: Literal['male', 'female']
    user_type: Literal['common', 'workflow_admin', 'super_admin']
    # creator: int

class SetPwd(BaseModel):
    """用户修改密码"""
    old_pwd: str
    new_pwd_1: str
    new_pwd_2: str

class SetWorkflow(BaseModel):
    """设置用户为工作流管理员"""
    job_id_list: List[str]

class SetCommon(BaseModel):
    """设置工作流管理员为普通用户"""
    job_id_list: List[str]

class GetDepart(BaseModel):
    """分页获得部门信息"""
    search_value: str = ''
    per_page: int = 10
    page: int = 1

class AddDepart(BaseModel):
    """增加部门"""
    name: str
    parent_depart_id: Optional[int]
    leader_id: Optional[int]
    approver_id: Optional[int]
    creator: int

class UpdateDepart(BaseModel):
    """更新部门"""
    depart_id: int
    name: str
    parent_depart_id: Optional[int]
    leader_id: Optional[int]
    approver_id: Optional[int]
    creator: int

class GetDepartRelateUser(BaseModel):
    """分页获得指定部门内的所有用户"""
    depart_id: int
    per_page: int = 10
    page: int = 1

class AddDepartRelateUser(BaseModel):
    """添加用户到指定部门"""
    depart_id: int
    job_id: List[str]
    creator: int

class ChangeRelationOfDepartAndUser(BaseModel):
    """更改部门和用户的关系（用户转部门）"""
    depart_id: int
    job_id: List[str]
    new_depart_id: int

class DeleteUserFromDepart(BaseModel):
    """从部门中删除用户"""
    depart_id: int
    job_id: List[str]

class GetJobtitle(BaseModel):
    """分页获得岗位信息"""
    search_value: str = ''
    per_page: int = 10
    page: int = 1

class AddJob(BaseModel):
    """增加岗位"""
    name: str
    description: str
    creator: int

class UpdateJob(BaseModel):
    """更新岗位"""
    jobtitle_id: int
    name: str
    description: str
    creator: int

class GetJobRelateUser(BaseModel):
    """分页获得指定岗位内的所有用户"""
    jobtitle_id: int
    per_page: int = 10
    page: int = 1

class AddJobRelateUser(BaseModel):
    """指定岗位添加用户"""
    jobtitle_id: int
    job_id: List[str]
    creator: int

class ChangeRelationOfJobAndUser(BaseModel):
    """更改岗位和用户的关系（用户转岗位）"""
    jobtitle_id: int
    job_id: List[str]
    new_jobtitle_id: int

class DeleteUserFromJob(BaseModel):
    """删除岗位里的用户"""
    jobtitle_id: int
    job_id: List[str]
