from django.http import HttpResponse
from django.shortcuts import render,redirect,reverse
if __name__ == '__main__':
    from ..core import core
else:
    from core import core


def action_search(request):
    request.encoding = 'utf-8'
    # 获取输入的学号和密码
    address = request.GET.get('address')
    # 查询地址信息
    res = core.search(int(address, 16))
    if res:
        found = True
        result = res
        # result = res.replace('\n', '<br>')
    else:
        found = False
        result = "无结果"
    return render(request, "index.html", {"found": found, "address": address, "result": result})
