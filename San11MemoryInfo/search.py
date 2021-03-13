from django.http import HttpResponse
from django.shortcuts import render,redirect,reverse
if __name__ == '__main__':
    from ..core import core
else:
    from core import core


def search(request):
    request.encoding = 'utf-8'
    ver = request.GET.get('ver')
    address = request.GET.get('address')
    name = request.GET.get('name')
    # 查询地址信息
    if address:
        res = core.search_address(ver, int(address, 16))
        value = address
        type_ = "addr"
        result_list = []
    elif name:
        result_list = core.search_name(ver, name)
        value = name
        type_ = "name"
        res = "结果：{}".format(len(result_list))
    else:
        res = ""
        value = ""
        type_ = ""
        result_list = []
    if res:
        found = True
        result = res
    else:
        found = False
        result = "无结果"
    return render(request, "search.html", {"found": found, "type": type_, "value": value,
                                           "result": result, "ver": ver, "result_list": result_list})
