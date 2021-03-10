from django.http import HttpResponse
from django.shortcuts import render
import re


html_hello = """
<h5>hello world!</h>
"""


def hello(request):
    return HttpResponse(html_hello)


def index(request):
    """首页"""
    if request.META.get('HTTP_X_FORWARDED_FOR'):
        ip = request.META.get("HTTP_X_FORWARDED_FOR")
    else:
        ip = request.META.get("REMOTE_ADDR")
    print("ip:", ip)
    return render(request, "index.html")


def login(request):
    """登录页面"""
    return render(request, "login.html")

