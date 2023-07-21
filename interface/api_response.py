import json
from django.http import HttpResponse

def response(code, msg='', data=''):
    """返回消息
    :param code
    :param msg
    :param data
    :return:
    """
    return HttpResponse(json.dumps(dict(code=code, msg=msg, data=data), ensure_ascii=False), content_type="application/json")
