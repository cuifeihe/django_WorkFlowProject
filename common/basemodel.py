from django.db import models

class TsInterfaceMixin(object):
    """将pydantic转换为Ts格式字符串"""
    @classmethod
    def get_ts_interface(cls, field_dict=None, field_is_list=False, indentation_form='\t', recursion_time=1): # 递归深度写进函数参数里，每次递归根据情况决定是否将深度加一
        result = 'interface ' + cls.__name__ + ' {\n' + cls.__get_ts_interface(field_dict, field_is_list, indentation_form, recursion_time) + '}'
        return result

    @classmethod
    def __get_ts_interface(cls, field_dict, field_is_list, indentation_form, recursion_time) -> str:

        pydantic2ts = {
            'int': 'number',
            'float': 'number',
            'str': 'string',
            'bool': 'boolean',
            # 'List': '[]',
        }
        if not field_dict:
            field_dict = cls.__fields__

        result = ''
        for k, v in field_dict.items():
            indent_depth = indentation_form * recursion_time
            if v._type_display() in pydantic2ts.keys():
                if field_is_list:
                    ts_field = indent_depth + f'{k}: {pydantic2ts.get(v._type_display())}[];\n'
                else:
                    ts_field = indent_depth + f'{k}: {pydantic2ts.get(v._type_display())};\n'
                result += ts_field

            elif v._type_display()[:4] == 'List':
                field_is_list = True
                sub_para = {}

                if len(v.sub_fields) == 1:
                    sub_para[k] = v.sub_fields[0]
                    # 另外起一个变量作为递归次数进行传参
                    new_recursion_time = recursion_time
                    sub_res = cls.__get_ts_interface(sub_para, field_is_list, indentation_form, new_recursion_time)
                    field_is_list = False # 列表flag及时复位
                    result += f'{sub_res}'
                else: # 不考虑列表元素中含多种数据类型的情况
                    pass

            else:
                # 对于自定义类型
                custom_field = v.type_.__fields__
                new_recursion_time = recursion_time + 1   # 注意！要另外起一个变量，把值传进去进行递归而不是在自身上面加一再把自身传进去
                custom_res = cls.__get_ts_interface(custom_field, False, indentation_form, new_recursion_time) # 注意及时把field_is_list = False传进去，以免上一级递归的flag影响（自定义字段同时是列表的情况）

                if field_is_list:
                    ts_field = indent_depth + f'{k}: ' + '{\n' + f'{custom_res}' + indent_depth + '}' + '[];\n'
                else:
                    ts_field = indent_depth + f'{k}: ' + '{\n' + f'{custom_res}' + indent_depth + '}' + ';\n'

                result += f'{ts_field}'
        return result



class BaseModel(models.Model):
    """基础信息模型"""
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建日期')
    update_time = models.DateTimeField(auto_now=True, verbose_name='最后更新日期')
    is_deleted = models.BooleanField(verbose_name='已删除', default=False)

    class Meta:
        abstract = True


