from typing import Type, Union, Dict, List, Tuple, Optional
import os
import xlrd
from xlrd.sheet import Sheet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, 'data')

structures: Dict[str, "Structure"] = {}


class PathNode:
    def __init__(self, name, type_name):
        self.name = name
        self.type_name = type_name
        self.index = -1
        self.shifting = 0

    def __str__(self):
        return f"{self.name} {self.type_name} {self.index} {self.shifting}"

    def __repr__(self):
        return self.__str__()


class SearchingPath:
    def __init__(self, address):
        self.target_address = address
        self.path = ""
        self.nodes = []
        self._base_address = 0

        self.current_address = self.current_shift

    def append_path(self, name, type_name):
        # self.path += '->' + name
        node = PathNode(name, type_name)
        self.nodes.append(node)

    def append_index(self, index):
        # self.path += '[{}]'.format(index)
        self.nodes[-1].index = index

    def add_shifting(self, shifting):
        """必须在append_path后使用"""
        self.nodes[-1].shifting += shifting
        self._base_address += shifting

    def base_address(self):
        return self._base_address

    def current_shift(self):
        return self.target_address - self._base_address


class Structure:
    def __init__(self, name):
        self.name = name
        self.struct_: List[MemoryUnit] = []


class MemoryUnit:
    Unknown = "Unknown"
    Padding = "Padding"
    Number = "Number"
    String = "String"
    AssemblyCode = "AssemblyCode"
    Other = "Other"
    Struct_ = "Struct"
    Types = ("Unknown", "Padding", "Number", "String", "AssemblyCode", "Other")

    __slots__ = ('type', 'struct', 'name', 'desc', 'address', 'array_len', 'unit_size', 'size')

    def __init__(self, type_name=None, address=0, name="", desc="", unit_size=4, array_len=1):
        self.type = type_name
        self.address = address
        self.name = name
        self.desc = desc
        self.unit_size = unit_size
        self.array_len = array_len
        self.size = unit_size * array_len

    def text(self):
        return "{} {}\n起始:{:x} 终止:{:x} \n长度:{}(d) \n({})".format(self.name, self.__class__.__name__, self.address,
                                                                 self.address + self.size, self.size, self.desc)

    def __str__(self):
        return "{},\t{},\t{:x},\t{};".format(self.__class__.__name__, self.name, self.address, self.size)

    def search_by_address(self, shifting, path: SearchingPath) -> Tuple[Union["MemoryUnit", int, None], SearchingPath]:
        """

        :param shifting:
        :param path:
        :return: -1：地址靠前，0：地址在内(找到)，1：地址靠后
        """
        print(
            f"find: 当前基址:{hex(path.base_address())},当前查询偏移:{hex(shifting)}, 查询对象所在偏移:{hex(self.address)}~{hex(self.address + self.size)}, 查询对象:{self.name}({self.__class__.__name__})")
        if self.address <= shifting:
            if self.address + self.size > shifting:  # 找到
                print('找到')
                path.append_path(self.name, self.type)
                path.add_shifting(self.address)
                # return self, path
            else:
                # print('没找到')
                return -1, path
        else:  # 找过头了
            # print('找过头了')
            return 1, path
        # Array
        if self.array_len > 1:  # 是数组
            # path.add_shifting(self.address)  # 数组首地址偏移(已经在super().search中添加)
            unit_size = self.unit_size
            print(1, hex(shifting), hex(self.address), hex(shifting - self.address))
            index, shifting = divmod(shifting - self.address, unit_size)
            path.append_index(index)
            path.nodes[-1].type_name = "Array"
            path.append_path(self.type, self.type)
            path.add_shifting(index * unit_size)  # 数组元素偏移
        else:
            # 重定位偏移
            shifting -= self.address
        # struct
        if self.type not in self.Types:  # 是结构体
            print("enter", hex(shifting), hex(self.address))
            structure = structures.get(self.type)
            if structure:  # 进入结构体
                for unit in structure.struct_:
                    res, path = unit.search_by_address(shifting, path)
                    if res == -1:
                        continue
                    elif res == 1:
                        return 1, path
                    else:
                        return res, path
            return None, path
        else:
            return self, path

    def search_by_name(self, name, results: list):
        if name in self.name:
            print('找到')
            results.append((hex(self.address).lstrip('0x'), self.name))
        if self.type not in self.Types:  # 是结构体
            structure = structures.get(self.type)
            if structure:  # 进入结构体
                for unit in structure.struct_:
                    unit.search_by_name(name, results)


class Array(MemoryUnit):
    """数组"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0
        self.unit: MemoryUnit = None  # 单位
        self.length: int = 0  # 数组长度

    def text(self):
        return "{} \n起始:{:x} 终止:{:x} \n长度:{}(d) [{}({})]*{} \n({})". \
            format(self.name, self.address, self.address + self.size, self.size,
                   self.unit.__class__.__name__, self.unit.size, self.length, self.desc)

    def search_by_address(self, shifting, path):
        res, path = super().search_by_address(shifting, path)
        if isinstance(res, MemoryUnit):
            # path.add_shifting(self.address)  # 数组首地址偏移(已经在super().search中添加)
            unit_size = self.unit.size
            print(hex(shifting), hex(self.address), hex(shifting - self.address))
            index, shifting = divmod(shifting - self.address, unit_size)
            print(hex(shifting), hex(self.address), unit_size, index, shifting)
            path.add_shifting(index * unit_size)  # 数组元素偏移
            path.path += "[{}]".format(index)
            print(path.path)
            res, path = self.unit.search_by_address(shifting, path)
        return res, path

    def search_by_name(self, name, path: SearchingPath) -> Tuple[Optional["MemoryUnit"], SearchingPath]:
        res, path = super().search_by_name(name, path)
        return res, path


class Struct(MemoryUnit):
    """结构体"""

    def __init__(self, name, desc, address):
        super().__init__()
        self.name = name
        self.desc = desc
        self.address = address
        self.size = 0
        self.structure: Optional[str] = None

    def search_by_address(self, shifting, path):
        """

        :param shifting:
        :return: -1：地址靠前，0：地址在内(找到)，1：地址靠后
        """
        res, path = super().search_by_address(shifting, path)
        if isinstance(res, MemoryUnit):
            # 进入结构体，重定位偏移
            print("enter", hex(shifting), hex(self.address))
            # path.add_shifting(self.address)  # 结构体首地址偏移(已经在super().search中添加)
            shifting -= self.address

            structure = structures.get(self.structure)
            if structure:  # 进入结构体
                for unit in structure.struct_:
                    res, path = unit.search_by_address(shifting, path)
                    if res == -1:
                        continue
                    elif res == 1:
                        return 1, path
                    else:
                        return res, path
        return res, path

    def search_by_name(self, name, path: SearchingPath) -> Tuple[Optional["MemoryUnit"], SearchingPath]:
        res, path = super().search_by_name(name, path)
        structure = structures.get(self.structure)
        if structure:  # 进入结构体
            for unit in structure.struct_:
                res, path = unit.search_by_name(name, path)
                if res:
                    return res, path
                else:
                    continue
        return None, path


main_unit_jp: MemoryUnit = MemoryUnit(None, 0, "内存", "pk1.1.1", 0xfffffff, 1)
main_unit_fz: MemoryUnit = MemoryUnit(None, 0, "内存", "pk1.1.0", 0xfffffff, 1)


def init():
    print(DIR_DATA)
    book = xlrd.open_workbook(os.path.join(DIR_DATA, "memory-info-pk1.1.1.xls"))
    struct_name = "San11"
    recursion_struct(main_unit_jp, book, struct_name)
    print(structures)
    # for structure in structures.values():
    #     for item in structure.struct_:
    #         print(item.__str__())

    # book = xlrd.open_workbook(os.path.join(DIR_DATA, "memory-info-pk1.1.0.xls"))
    # struct_name = "san11"
    # recursion_struct(main_unit_fz, book, struct_name)


def search_address(ver, address):
    if ver == 'JP':
        res, path = main_unit_jp.search_by_address(address, SearchingPath(0))
    elif ver == 'FZ':
        res, path = main_unit_fz.search_by_address(address, SearchingPath(0))
    else:
        print("版本异常")
        return ""
    if isinstance(res, MemoryUnit):
        str_path = ""
        bytes_left = address - path.base_address()
        base_adr = 0
        for i in range(len(path.nodes)):
            node = path.nodes[i]
            name = node.name
            type_ = node.type_name
            index = node.index
            base_adr += node.shifting
            if isinstance(type_, str):
                indent = "---"*i
                str_path += f"""<br>{indent}-> <span style="color: #888888;"><strong>{type_}</strong></span>""" \
                            f"""<span>({name})</span>"""
            if index >= 0:
                str_path += f"""<span style="color: #00aaff;">[{index}]</span>"""
            str_path += f"""<span style="font-size:9pt; color: #444444">({base_adr:x})</span>"""
        str_path += f""" + {bytes_left} </br>"""

        start_address = path.base_address()
        ended_address = path.base_address() + res.size
        str_res = str_path
        str_res += f"<br>地址 <strong>( {address:x} )</strong> 在以下内存段中：<br>" \
                   f"【{res.name}】 {res.desc}<br>起始地址: <strong>[ {start_address:x} ]</strong> , " \
                   f"结束地址: <strong>[ {ended_address:x} ]</strong> , 长度: {res.size} 字节<br>"
        print(path.nodes)
        return str_res
    else:
        print("未找到结果")
        return ""


def search_name(ver, name):
    res = []
    if ver == 'JP':
        main_unit_jp.search_by_name(name, res)
    elif ver == 'FZ':
        main_unit_fz.search_by_name(name, res)
    else:
        print("版本异常")
        return None
    if res:
        return res
    else:
        print("未找到结果")
        return None


def recursion_struct(upper_unit: MemoryUnit, book, type_name: str):
    structure: Structure = structures.get(type_name)
    if structure:  # 已经解析过的结构体
        upper_unit.type = type_name
        return
    else:
        structure = Structure(type_name)
        structures[type_name] = structure
        try:
            sheet = book.sheet_by_name(type_name)  # 找到结构体结构
            upper_unit.type = type_name
        except xlrd.biffh.XLRDError:
            print("没有<{}>".format(type_name))
            upper_unit.type = MemoryUnit.Unknown
            return
        for row in range(1, sheet.nrows - 1):  # 除去第一行标题和最后一行总和
            address, type_, name, desc, unit_size, array_len = sheet.row_values(row, 0, 6)
            # 相对地址偏移
            if isinstance(address, (int, float)):
                address = int(address)
            elif address and isinstance(address, str):
                address = int(address, 16)
            else:
                continue
            # 单位长度、数组长度
            unit_size = int(unit_size)
            if array_len:
                array_len = int(array_len)
            else:
                array_len = 1
            # 存入结构体
            if not name:
                name = "blank"
            memory_unit = MemoryUnit(None, address, name, desc, unit_size, array_len)
            # 数据类型
            if type_ == '':
                type_ = "Number"
            type_name: str = type_.capitalize()
            if type_name not in MemoryUnit.Types:  # 没有对应的类型，可能是结构体
                # memory_unit.type = type_name  # 在下面的函数里赋值
                recursion_struct(memory_unit, book, type_name)
            else:
                memory_unit.type = type_name
            structure.struct_.append(memory_unit)
        # 获取结构体大小
        # struct_size = sheet.cell_value(sheet.nrows - 1, 1)
        # print('struct_size', struct_size)
        # if isinstance(struct_size, (int, float)):
        #     struct_size = int(struct_size)
        # elif isinstance(struct_size, str):
        #     if struct_size:
        #         struct_size = int(struct_size, 16)
        #     else:
        #         struct_size = 0
        # else:
        #     struct_size = None
        # upper_unit.unit_size = struct_size
        # upper_unit.size = upper_unit.array_len * struct_size


# if __name__ == '__main__':
init()
search_address('JP', 0x7224bb8 + 56)
# scenario = structures.get('Scenario')
# for st in scenario.struct_:
#     print(st)
