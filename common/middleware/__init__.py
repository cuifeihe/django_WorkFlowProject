from django.utils.deprecation import MiddlewareMixin
import json
from django.http import JsonResponse, HttpResponse, HttpRequest
import sys
from django.conf import settings
from django.views.debug import technical_404_response, technical_500_response

class JsonDataMiddleware(MiddlewareMixin):
    """中间件将请求体Json数据取出"""
    def process_request(self, request: HttpRequest):
        json_str = request.body
        if request.method in ['GET']:
            return

        else:
            if request.META.get('CONTENT_TYPE') == 'application/json':
                if int(request.META.get('CONTENT_LENGTH')) > 0:
                    if isinstance(json_str, bytes):
                        json_decode = json_str.decode()
                        data = json.loads(json_decode)
                        request.data = data
                    else:
                        request.data = {}
                else:
                    request.data = {}
            elif request.META.get('CONTENT_TYPE') == 'application/x-www-form-urlencoded':
                # print(request.body)
                request.data = getattr(request.POST, 'dict')()
            else:
                return


class CustomExceptionMiddleware:
    """在非debug模式下，使用中间件拦截异常"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if request.user.is_superuser: # or request.META.get('REMOTE_ADDR') in settings.ADMIN_IP:
            return technical_500_response(request, *sys.exc_info())
        return technical_404_response(request, exception)