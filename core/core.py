from typing import Type, Union, Dict, List, Tuple, Optional
import os
import xlrd
from xlrd.sheet import Sheet

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(BASE_DIR, 'data')

structures: Dict[str, "Structure"] = {}


class Structure:
    def __init__(self, name):
        self.name = name
        self.struct_: List[MemoryUnit] = []


class SearchingPath:
    def __init__(self, address):
        self.target_address = address
        self.path = ""
        self._address = []
        self._base_address = 0

        self.current_address = self.current_shift

    def append_path(self, path):
        self.path += '->' + path

    def add_shifting(self, shifting):
        self._address.append(shifting)
        self._base_address += shifting

    def base_address(self):
        return self._base_address

    def current_shift(self):
        return self.target_address - self._base_address

    def address(self):
        ret = []
        for a in self._address:
            ret.append(hex(a))
        return ret


class MemoryUnit:
    def __init__(self):
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0

    def text(self):
        return "{} {}\n起始:{:x} 终止:{:x} \n长度:{}(d) \n({})".format(self.name, self.__class__.__name__, self.address,
                                                                 self.address + self.size, self.size, self.desc)

    def __str__(self):
        return "{},\t{},\t{:x},\t{};".format(self.__class__.__name__, self.name, self.address, self.size)

    def search(self, shifting, path: SearchingPath) -> Tuple[Union["MemoryUnit", int], SearchingPath]:
        print(
            f"find: 当前基址:{hex(path.base_address())},当前查询偏移:{hex(shifting)}, 查询对象所在偏移:{hex(self.address)}~{hex(self.address + self.size)}, 查询对象:{self.name}({self.__class__.__name__})")
        if self.address <= shifting:
            if self.address + self.size > shifting:  # 找到
                print('找到')
                path.add_shifting(self.address)
                path.append_path(self.name)
                return self, path
            else:
                # print('没找到')
                return -1, path
        else:  # 找过头了
            # print('找过头了')
            return 1, path


class Unknown(MemoryUnit):
    """未知"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0


class Padding(MemoryUnit):
    """空白"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0


class Number(MemoryUnit):
    """数值"""

    def __init__(self, name="", desc="", address=0, size=0):
        super().__init__()
        self.name = name
        self.desc = desc
        self.address = address
        self.size = size


class String(MemoryUnit):
    """字符串"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0


class AssemblyCode(MemoryUnit):
    """汇编码"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0


class Other(MemoryUnit):
    """其他类型"""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.desc = ""
        self.address = 0
        self.size = 0


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

    def search(self, shifting, path):
        res, path = super().search(shifting, path)
        if isinstance(res, MemoryUnit):
            # path.add_shifting(self.address)  # 数组首地址偏移(已经在super().search中添加)
            unit_size = self.unit.size
            print(hex(shifting), hex(self.address), hex(shifting - self.address))
            index, shifting = divmod(shifting - self.address, unit_size)
            print(hex(shifting), hex(self.address), unit_size, index, shifting)
            path.add_shifting(index * unit_size)  # 数组元素偏移
            path.path += "[{}]".format(index)
            print(path.path)
            res, path = self.unit.search(shifting, path)
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

    def search(self, shifting, path):
        """

        :param shifting:
        :return: -1：地址靠前，0：地址在内(找到)，1：地址靠后
        """
        res, path = super().search(shifting, path)
        if isinstance(res, MemoryUnit):
            # 进入结构体，重定位偏移
            print("enter", hex(shifting), hex(self.address))
            # path.add_shifting(self.address)  # 结构体首地址偏移(已经在super().search中添加)
            shifting -= self.address

            structure = structures.get(self.structure)
            if structure:  # 进入结构体
                for unit in structure.struct_:
                    res, path = unit.search(shifting, path)
                    if res == -1:
                        continue
                    elif res == 1:
                        return 1, path
                    else:
                        return res, path
        return res, path


TYPES = {
    "Unknown": Unknown,
    "Padding": Padding,
    "Number": Number,
    "String": String,
    "AssemblyCode": AssemblyCode,
    "Other": Other,
    "Array": Array,
}

main_unit: Struct = Struct("San11", "主体", 0)


def init():
    print(DIR_DATA)
    book = xlrd.open_workbook(os.path.join(DIR_DATA, "memory-info-pk1.1.1.xls"))
    struct_name = "san11"
    recursion_struct(main_unit, book, struct_name)
    print(structures)
    # for structure in structures.values():
    #     for item in structure.struct_:
    #         print(item.__str__())


def search(address):
    res, path = main_unit.search(address, SearchingPath(0))
    if isinstance(res, MemoryUnit):
        print(res.text())
        str_res = ("查询地址: [ {:x} ] \n".format(address) +
                   "{}({}) + {:x}\n".format(path.path, res.__class__.__name__, address - path.base_address()) +
                   "{{{}}}起始地址: [ {:x} ] , 结束地址: [ {:x} ] , 变量(代码段)长度:{}\n".format(res.name, path.base_address(),
                                                                       path.base_address() + res.size, res.size))
        str_res += "路径偏移:" + " + ".join(path.address()) + " (+ {:x})".format(address - path.base_address())
        return str_res
    else:
        print("未找到结果")
        return ""


def recursion_struct(struct: Struct, book, type_name: str):
    structure: Structure = structures.get(type_name)
    if structure:  # 已经解析过的结构体
        struct.structure = type_name
    else:
        structure = Structure(type_name)
        structures[type_name] = structure
        try:
            sheet = book.sheet_by_name(type_name)  # 找到结构体结构
            struct.structure = type_name
        except xlrd.biffh.XLRDError:
            print("没有<{}>".format(type_name))
            struct.structure = None
        else:
            for row in range(1, sheet.nrows - 1):  # 除去第一行标题和最后一行总和
                address, size, type_, name, desc, unit, length = sheet.row_values(row, 0, 7)
                # 相对地址偏移
                if isinstance(address, (int, float)):
                    address = int(address)
                elif address and isinstance(address, str):
                    address = int(address, 16)
                else:
                    continue
                # 数据长度
                if isinstance(size, (int, float)):
                    size = int(size)
                elif isinstance(size, str):
                    if size:
                        size = int(size, 16)
                    else:
                        size = 0
                else:
                    size = None
                # 数据类型
                if type_ == '':
                    item = Number()
                else:
                    type_name: str = type_.capitalize()
                    Type_ = TYPES.get(type_name)
                    if Type_ is None:  # 没有对应的类型，可能是结构体
                        item = Struct("", "", 0)
                        recursion_struct(item, book, type_name)
                    else:
                        item = Type_()
                        if isinstance(item, Array):  # Array类型
                            item.length = int(length)
                            if not unit:
                                raise ValueError
                            elif isinstance(unit, (int, float)):  # 十进制长度
                                item.unit = Number("Number", size=int(unit))
                            elif isinstance(unit, str):
                                if unit.startswith('0x'):  # 16进制长度
                                    item.unit = Number("Number", size=int(unit, 16))
                                else:  # 结构体
                                    unit_struct = Struct(str(unit), "", 0)  # 数组内的结构体
                                    # unit_struct.size = size // item.length
                                    item.unit = unit_struct
                                    recursion_struct(unit_struct, book, unit)
                            else:
                                raise ValueError
                if not name:
                    name = "blank"
                item.name = name
                item.desc = desc
                item.address = address
                item.size = size
                structure.struct_.append(item)
            # 结构体大小
            address, struct_size = sheet.row_values(sheet.nrows - 1, 0, 2)
            if isinstance(struct_size, (int, float)):
                struct_size = int(struct_size)
            elif isinstance(struct_size, str):
                if struct_size:
                    struct_size = int(struct_size, 16)
                else:
                    struct_size = 0
            else:
                struct_size = None
            struct.size = struct_size


# if __name__ == '__main__':
init()
search(0x7224bb8 + 3)
