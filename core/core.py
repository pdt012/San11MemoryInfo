from typing import Type, Union, Dict, List, Tuple, Optional
from enum import Enum
import os
import xlrd
from xlrd.sheet import Sheet


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, 'data')


class SearchingPath:
    class PathNode:
        def __init__(self):
            ...

    def __init__(self):
        ...


class MemUnitType(Enum):
    NoRecord,  # 未研究
    Unknown,  # 未知
    Padding,  # 留白
    Integer,  # 整型(包括char, short, int)
    CharSet,  # 字符串
    Function,  # 函数(汇编)
    Other  # 其它


class BaseMemoryUnit:
    def __init__(self, name="", desc=""):
        self.name = name
        self.desc = desc

    def get_start(self):
        """起始地址(包含)"""
        return self.relative_addr
    
    def get_end(self):
        """结束地址(不包含)"""
        return self.relative_addr + self.get_size()
        
    def get_size(self):
        return 0
    
    def search_by_address(self, path: SearchingPath):
        


class MemoryUnit(BaseMemoryUnit):
    def __init__(self, type_: MemUnitType, size: int, name: str, desc: str = "")
        super().__init__("未知", desc)
        self.type = type_
        self.size = size
        
    def get_type(self):
        return self.type
        
    def get_size(self):
        return self.size
        
    def search_by_address(self, path: SearchingPath):
        shift = path.abs_addr - path.base_address  # 相对起始位置的偏移地址
        # 该数据信息加入path
        return


class Function(MemoryUnit):
    def __init__(self, size, name, desc="")
        super().__init__(MemUnitType.Function, size, name, desc)
        

class Array(BaseMemoryUnit):
    def __init__(self, element, array_len, name, desc=""):
        super().__init__(name, desc)
        self.element: BaseMemoryUnit = element  # 元素类型
        self.array_len: int = array_len  # 数组长度

    def get_type(self):
        return MemUnitType.Array

    def get_size(self):
        return self.element.get_size() * self.array_len

    def search_by_address(self, path: SearchingPath):
        shift = path.abs_addr - path.base_address  # 相对数组起始位置的偏移地址
        index, mod = divmod(shift, self.element.get_size())
        # path 内添加该元素节点
        # 进入该元素继续查找
        return element.search_by_address(path)

    
class Struct(BaseMemoryUnit):
    """结构体"""
    
    def __init__(self, struct_name, name, desc, declared_size):
        super().__init__(name, desc)
        self.struct_name: str = struct_name
        self.properties: Dict[int, BaseMemoryUnit] = {}
        self.declared_size: int = declared_size # 在Excel structs页定义的struct大小，而不是根据所有属性计算得出的大小(这样可以允许漏写一些属性)

    def get_type(self):
        return MemUnitType.Struct
        
    def get_size(self):
        return self.declared_size

    def search_by_address(self, path: SearchingPath):
        for relative_addr, property_ in self.properties.items():
            start_addr = path.base_address + relative_addr
            end_addr = start_addr + property_.get_size()
            if start_addr <= path.abs_addr < end_addr:  # 找到
                # path 内添加该属性节点
                # 进入该属性继续查找
                return property_.search_by_address(path)


class Memory(Struct):
    def __init__(self):
        super().__init__("San11", 0, "内存", "")
        self.structs: Dict[str, MemoryUnit] = {}  # 结构体字典
        
        self.book = None
        
    def init(self):
        self.book = xlrd.open_workbook(os.path.join(DIR_DATA, "pk1.1.1", "structs.xls"))
        try:
            sheet = self.book.sheet_by_name("structs")  # 结构体定义页
        except xlrd.biffh.XLRDError:
            print("没有<structs>页")
            return None
        for row in range(1, sheet.nrows - 1):  # 除去第一行标题
            struct_name, name, desc, size = sheet.row_values(row, 0, 4)
            self.structs[struct_name] = Struct(struct_name, name, desc, size)
            self.find_struct_properties(main_unit_jp, struct_name)
        
    def find_struct_properties(self, struct: Struct):
        try:
            sheet = self.book.sheet_by_name(type_name)  # 找到结构体结构
        except xlrd.biffh.XLRDError:
            print("没有<{}>".format(type_name))
            return None
        for row in range(1, sheet.nrows):  # 除去第一行标题
            address, type_name, name, desc, element_size, array_len = sheet.row_values(row, 0, 6)
            if not type_name:
                type_name = MemUnitType.Integer.name
            if type_name in MemUnitType.__members__:  # 基本类型
                element = MemoryUnit(MemUnitType[type_name], address, element_size, name, desc)
            else:  # 结构体 Struct
                element = self.structs.get(type_name)
                if not element:
                    # 没有定义的结构体
                    print("类型<{}>未定义".format(type_name))
                    continue
                if address in struct.properties:
                    #地址重复
                    print("类型<{}>地址{}重复定义".format(struct_name, hex(type_name)))
                else:
                    if array_len:  # 数组Array型
                        array_len = int(array_len)
                        struct.properties[address] = Array(element, array_len, name, desc)
                    else:
                        struct.properties[address] = element
    

if __name__ == '__main__':
    init()
