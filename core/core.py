# -*- coding: utf-8 -*-
from typing import Type, Union, Dict, List, Tuple, Optional
from enum import Enum
import os
import xlrd
from xlrd.sheet import Sheet


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, 'data')
PATH_STRUCTS = os.path.join(DIR_DATA, "pk1.1.1", "structs.xls")
DIR_FUNCTIONS = os.path.join(DIR_DATA, "pk1.1.1", "functions")


class SearchingPath:
    class Node:
        def __init__(self, absolute_addr: int, relative_shift: int, unit: "BaseMemoryUnit"):
            self.absolute_addr = absolute_addr  # absolute address in memory of the start of unit
            self.relative_shift = relative_shift  # relative address in parent struct of the start of unit
            self.unit = unit

    def __init__(self, root_unit: "BaseMemoryUnit", target_addr):
        self.target_addr = target_addr
        self.nodes: List[SearchingPath.Node] = [SearchingPath.Node(0, 0, root_unit)]

    def last_node(self) -> "SearchingPath.Node":
        return self.nodes[-1]

    def add_node(self, node: "SearchingPath.Node"):
        self.nodes.append(node)

    def __str__(self) -> str:
        res = ""
        res += f"TARGET ADDRESS: {hex(self.target_addr)}"
        indent = ""
        for i in range(1, len(self.nodes)):
            node = self.nodes[i]
            indent += " "
            unit = node.unit
            res += "\n" + indent + f"-> [{node.absolute_addr:x}] {str(unit)}"
            if isinstance(unit, Array):
                base_addr = node.absolute_addr  # 数组起始地址
                shift = self.target_addr - base_addr  # 目标地址相对数组起始位置的偏移
                index = shift // unit.element.get_size()
                res += f" index[{index}]"
        last_node = self.last_node()
        last_unit = last_node.unit
        if (isinstance(last_unit, Function) and not last_unit.desc):
            last_unit.load_desc()
        shift = self.target_addr-last_node.absolute_addr
        res += f"\nRESULT: [{last_node.absolute_addr:x}]+{hex(shift)} {last_unit.get_detail()}"
        return res
        
    def __repr__(self) -> str:
        return str(self)


class MemUnitType(Enum):
    NoRecord = 0,  # 未收录
    Unknown = 1,  # 未知
    Padding = 2,  # 留白
    Integer = 3,  # 整型(包括char, short, int)
    CharSet = 4,  # 字符串
    Function = 5,  # 函数(汇编)
    Other = 6  # 其它


class BaseMemoryUnit:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc

    def get_type_str(self) -> str:
        return "BaseMemoryUnit"
        
    def get_size(self):
        return 0
    
    def search_by_address(self, path: SearchingPath):
        ...

    def get_detail(self) -> str:
        return self.__str__() + f" (size={hex(self.get_size())})"

    def __str__(self) -> str:
        return f"<{self.get_type_str()}> {self.name}"

    def __repr__(self) -> str:
        return str(self)


class MemoryUnit(BaseMemoryUnit):
    def __init__(self, type_: MemUnitType, size: int, name: str, desc: str):
        super().__init__(name, desc)
        self.type = type_
        self.size = size
        
    def get_type_str(self):
        return self.type.name
        
    def get_size(self):
        return self.size
        
    def search_by_address(self, path: SearchingPath):
        shift = path.last_node().relative_shift  # 相对起始位置的偏移地址
        return

    def get_detail(self) -> str:
        res = super().get_detail()
        if self.desc:
            res += "\n" + self.desc
        return res
    
    
class Function(MemoryUnit):
    def __init__(self, name, filepath, size = 0x10):
        super().__init__(MemUnitType.Function, size, name, "")
        self.filepath = filepath
        # self.start_addr = start_addr
        
    def load_desc(self):
        try:
            with open(os.path.join(DIR_FUNCTIONS, self.filepath), encoding="utf-8") as fp:
                firstline = fp.readline()  # 跳过第一行的函数信息
                self.desc = fp.read().strip()
        except OSError:
            error(f"函数资料文件读取失败 <{path}>")


class Array(BaseMemoryUnit):
    """数组"""

    def __init__(self, element, array_len, name, desc):
        super().__init__(name, desc)
        self.element: BaseMemoryUnit = element  # 元素类型
        self.array_len: int = array_len  # 数组长度

    def get_type_str(self) -> str:
        return "Array"

    def get_size(self):
        return self.element.get_size() * self.array_len

    def search_by_address(self, path: SearchingPath):
        base_addr = path.last_node().absolute_addr  # 数组起始地址
        shift = path.target_addr - base_addr  # 目标地址相对数组起始位置的偏移
        index, mod = divmod(shift, self.element.get_size())
        # path 内添加该元素节点
        element_start_shift = shift - int(mod)  # 该元素相对数组起始位置的偏移
        element_start_absolute_addr = base_addr + element_start_shift  # 该元素起始地址
        path.add_node(path.Node(element_start_absolute_addr, element_start_shift, self.element))
        # 进入该元素继续查找
        return self.element.search_by_address(path)

    def get_detail(self) -> str:
        res = super().get_detail() + f"[len={self.array_len}]"
        if self.desc:
            res += "\n" + self.desc
        return res

    
class Struct(BaseMemoryUnit):
    """结构体"""
    
    def __init__(self, struct_name, name, desc, declared_size):
        super().__init__(name, desc)
        self.struct_name: str = struct_name
        self.properties: Dict[int, BaseMemoryUnit] = {}  # relative_addr -> unit
        self.declared_size: int = declared_size # 在Excel structs页定义的struct大小，而不是根据所有属性计算得出的大小(这样可以允许漏写一些属性)

    def get_type_str(self) -> str:
        return self.struct_name

    def get_size(self):
        return self.declared_size

    def search_by_address(self, path: SearchingPath):
        base_addr = path.last_node().absolute_addr

        for relative_shift in sorted(self.properties.keys(), reverse=True):  # 从后往前
            unit = self.properties[relative_shift]
            start_addr = base_addr + relative_shift
            if start_addr <= path.target_addr:
                end_addr = start_addr + unit.get_size()
                if path.target_addr < end_addr:  # 找到
                    # path 内添加该属性节点
                    path.add_node(path.Node(start_addr, relative_shift, unit))
                    # 进入该属性继续查找
                    return unit.search_by_address(path)
                else:  # 找过头
                    return


class Memory(Struct):
    def __init__(self):
        super().__init__("San11", "内存", "", 0x10000000)
        self.structs: Dict[str, MemoryUnit] = {}  # 结构体字典
        
        self.book = None
        
    def init(self):
        self.book = xlrd.open_workbook(PATH_STRUCTS)
        try:
            sheet: Sheet = self.book.sheet_by_name("structs")  # 结构体定义页
        except xlrd.biffh.XLRDError:
            print("没有<structs>页")
            return None
        for row in range(1, sheet.nrows):  # 除去第一行标题
            struct_name, name, desc, size = sheet.row_values(row, 0, 4)
            struct = Struct(struct_name, name, desc, int(size))
            self.structs[struct_name] = struct
        for struct in self.structs.values():
            self.load_struct_properties(struct)  # 加载结构体的属性定义
        self.load_struct_properties(self)  # 加载主内存结构
        # 加载函数资料
        for dirname, dirs, files in os.walk(DIR_FUNCTIONS, topdown=False):  # 递归遍历全部文件
            for filename in files:
                path = os.path.join(dirname, filename)
                try:
                    with open(os.path.join(dirname, filename), encoding="utf-8") as fp:
                        firstline = fp.readline().rstrip()  # 读第一行的函数信息
                        ls = firstline.split()
                        if len(ls) == 2:
                            name, addr = ls
                            size = "0x10"
                        elif len(ls) == 3:
                            name, addr, size = ls
                        else:
                            raise ValueError()
                        addr = int(addr, 16)
                        size = int(size, 16)
                        func = Function(name, path, size)
                        self.properties[addr] = func
                except OSError:
                    error(f"函数资料文件读取失败 <{path}>")
                except (ValueError, TypeError):  # 格式有误
                    error(f"函数资料解析错误 <{path}> \"{firstline}\"")
                
    def load_struct_properties(self, struct: Struct):
        try:
            sheet: Sheet = self.book.sheet_by_name(struct.struct_name)  # 找到结构体结构
        except xlrd.biffh.XLRDError:
            print("没有<{}>".format(struct.struct_name))
            return None
        for row in range(1, sheet.nrows):  # 遍历结构体内属性
            address, property_type_name, name, desc, unit_size, array_len = sheet.row_values(row, 0, 6)
            address = int(address, 16)
            unit_size = int(unit_size)
            if not property_type_name:
                property_type_name = MemUnitType.Integer.name  # 默认Integer型
            if property_type_name in MemUnitType.__members__:  # 基本类型
                unit = MemoryUnit(MemUnitType[property_type_name], unit_size, name, desc)
            else:  # 结构体 Struct
                unit = self.structs.get(property_type_name)
                if not unit:  # 没有定义的结构体
                    print("类型<{}>未定义".format(property_type_name))
                    continue
                elif unit.get_size() >= struct.get_size():  # 子结构体大小大于父结构体
                    raise TypeError("类型嵌套不合理<{}>in<{}>".format(property_type_name, struct.struct_name))  # 避免无限嵌套
            if address in struct.properties:  # 地址重复
                print("类型<{}>地址{}重复定义".format(property_type_name, hex(property_type_name)))
            else:
                if array_len:  # 数组Array型
                    array_len = int(array_len)
                    struct.properties[address] = Array(unit, array_len, name, desc)
                else:
                    struct.properties[address] = unit


def error(text):
    print("Error:", text)


if __name__ == '__main__':
    memory = Memory()
    memory.init()

    print("========= test =========")
    path = SearchingPath(memory, 0x7224BB8+ 56)
    memory.search_by_address(path)
    print(path)
    print("========================")

    while True:
        address = input("input address (hex) >>>")
        if address == "exit":
            break
        try:
            path = SearchingPath(memory, int(address, 16))
            memory.search_by_address(path)
            print(path)
        except Exception:
            continue

