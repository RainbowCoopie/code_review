import copy
import json
import math
from functools import reduce
from pprint import pprint
from array import array
from inspect import isfunction

from PIL import Image


class RStruct:
    """

    将 dict 转为 python 对象

    该类用于通过字典返回一个符合映射关系的 python 对象, 可以多次递归:
        struct().load(dict): 根据dict创建一个struct对象
        struct().dump(): 将struct对象格式化为json结构, 以字典类型进行返回
        struct().clean(): 清空struct()对象所有属性
        struct().detail(): 打印struct()对象中所有的详细属性
        ------------------------------
        python类型与json类型的转换规则表
        ------------------------------
        python      -> json     -> python:
        ------------------------------
            str     -> string   -> str
            int     -> number   -> int
            bool    -> bool     -> bool
            None    -> null     -> None
            list    -> array    -> list
            tuple   -> array    -> list
            dict    -> object   -> dict
        ------------------------------
    """
    # 异常处理字典
    d_exception = {
        "parameter_dict": f"Rainbow's tips: Parameter can only be dict!!",
        "parameter_basetype": f"Rainbow's tips: Parameter can only be basetype!!",
        "other": f"Rainbow's tips:",
    }

    def __init__(self, init_data: dict = None):
        """ 创建实例对象 """
        if isinstance(init_data, dict):  # data参数为dict类型: 调用load()方法创建其属性
            self.load(init_data)
        elif init_data:  # 存在data参数且类型不为dict: 抛出异常
            tips = f"{RStruct.d_exception['parameter_dict']}"
            raise Exception(tips)

    def clean(self):
        """ clean self attribute """
        for attrib in list(self.__dict__.keys()):
            exec(f"del self.{attrib}")

    def detail(self, sp=10):
        """ show detail --> self """
        # 回环嵌套: 递归
        def _recursion(_obj=None, _attrib=None, _level=0, _sp=sp):
            print(f"{' ' * _level * _sp}∟  {_attrib + ' --> ' if _attrib else ''}{repr(_obj)}")  # print
            if isinstance(_obj, type(RStruct())):  # 处理Struct()对象
                for attrib, v in _obj.__dict__.items():
                    _recursion(_obj=v, _attrib=attrib, _level=_level + 1)
            if isinstance(_obj, list):  # 处理列表
                for e in _obj:
                    _recursion(_obj=e, _level=_level + 1)
            if isinstance(_obj, dict):  # 处理字典
                for k, v in _obj.items():
                    _recursion(_obj=v, _attrib=k, _level=_level + 1)
        _recursion(_obj=self)

    def load(self, d_data: dict = None, protection: list = None):
        """
        d_data: 需要对象化的字典数据
        protection: 受保护属性列表, 箬属性名字在此列表中, 该属性的值不会被对象化
        """
        # 变量验证
        if not isinstance(d_data, dict):  # 判断并抛出异常
            tips = f"{RStruct.d_exception['parameter_dict']}"
            print(d_data)
            raise Exception(tips)
        prot = protection or []  # 变量初始化

        # 回环嵌套: 递归
        def _recursion(_d_data, _prot, _isprot=False):
            if isinstance(_d_data, dict):  # 处理字典, 若该字典受保护, 则返回处理后的字典, 否则返回Struct()对象
                _result = {} if _isprot else RStruct()
                for k, v in _d_data.items():
                    b_switch = True if k in _prot else False  # 判断当前值是否是受保护的值
                    res = _recursion(_d_data=v, _prot=_prot, _isprot=b_switch)
                    if _isprot:
                        _result[k] = res
                    else:
                        _result.__dict__.update({k: res})
            elif isinstance(_d_data, list):  # 处理列表, 返回处理后的列表
                _result = []
                for e in _d_data:
                    res = _recursion(_d_data=e, _prot=_prot)
                    _result.append(res)
            elif isinstance(_d_data, (str, int, bool, float, bytes, type(None))):  # 处理json格式中的标准类型, 原值返回用于构建字典/列表/Struct()
                _result = _d_data
            else:
                _tips = f"{RStruct.d_exception['parameter_basetype']}"
                raise Exception(_tips)
            return _result

        # 调用递归函数
        for k, v in _recursion(_d_data=d_data, _prot=prot).__dict__.items():  # 将结果赋值给实例对象
            self.__dict__.update({k: v})


class RGenerator:
    """ R生成器对象 """

    def __init__(self, items, max_len: int = 32):
        items = list(items)  # 将传入的对象类型变成列表
        if len(items) > max_len:  # 列表超长抛出异常
            raise Exception(f"列表长度不可超过 max_len = {max_len}")

        items = items[::-1]  # 列表倒序排列: 因为loop套娃的逻辑, 要使原迭代对象顺序输出, 需要从后往前进行套娃

        # generator = [None] + [{"data": item, "loop": None} for item in items]
        # generator[0] = generator[-1]
        generator = [{"data": item, "loop": None} for item in items]
        generator.append(generator[0])  # 将可迭代对象的末尾对象设置为R生成器的首位对象, 因为next()函数在第一次执行的时候会略过首位

        def _loop(child_dic, father_dic):
            """ 将 child_dic作为 loop的值赋给 father_dic """
            father_dic["loop"] = child_dic
            return father_dic

        generator = reduce(_loop, generator)

        self.__generator = generator
        print(generator)

    def next(self):
        self.__generator = self.__generator["loop"]  # 生成器指向下一个对象
        return self.__generator["data"]  # 返回生成器所指向的对象


def dump(d_data, turn_json=False, has_tuple=True, _print=False):
    """
    拆解obj的属性和值
    turn_json == False : return all attribute of the object --> dict  # 若为False, 返回结果为字典类型
    turn_json == True : return all attribute of the object --> json  # 若为True, 返回结果为json类型
    has_tuple == True : 可以拆解元组类型, 但是不支持转 json格式,
    _print == Ture : dump对象之后将字典格式的数据规范打印出来
    _top: is recursive top level  # 判断是否为顶层函数, 用于处理最终return, 仅有首次调用函数时_top=True, 递归过程中始终_top=False
    """
    def _process(_v):
        # set, tuple类型报错; str, int, bool, type(None)类型直接返回存储; 其他类型(obj)进行递归
        if isinstance(_v, (set, tuple)) and not has_tuple:
            _tips = f"{RStruct.d_exception['parameter_basetype']}"
            raise Exception(_tips)

        if not isinstance(_v, (str, int, bool, float, bytes, type(None))):
            _v = _recursion(_o_data=_v)
        return _v

    def _recursion(_o_data):
        _result = {}
        # recursive tuple
        if has_tuple:
            if isinstance(_o_data, tuple):
                _result = tuple(_process(e) for e in _o_data)
        # recursive dict
        if isinstance(_o_data, dict):
            _result = {k: _process(v) for k, v in _o_data.items()}
        # recursive list
        if isinstance(_o_data, list):
            _result = [_process(e) for e in _o_data]
        # recursive obj
        if not isinstance(_o_data, (list, dict, tuple)):
            try:
                _result = {a: _process(v) for a, v in _o_data.__dict__.items()}

            except Exception as e:
                for arr in _o_data.__dir__():
                    if eval(f"callable(_o_data.{arr})"):
                        pass
                    if eval(f"isfunction(_o_data.{arr})"):
                        pass
                    if arr[0:2] == "__" and arr[-2:] == "__":
                        pass
                    else:
                        v = eval(f"_o_data.{arr}")
                        _result[arr] = _process(v)
        return _result
    result = json.dumps(_recursion(d_data)) if turn_json else _recursion(d_data)

    if _print is True:
        pprint(result)
    return result


def calcsys(num: int, sys: int) -> list[str]:
        """
        原数据为十进制的num, 转换为sys进制, 输出其存放十进制表达的单值的列表
        test = calcsys(999, 8)  # 将十进制的 999 转换为 8 进制
        """
        # @Wrapper.clock
        def _recursion(_num: int, _result: list):
            """ _recursion: Calculated System Recurrence """
            power = (int(math.log(_num, sys)))  # 最大指数, 同时也是当前值指向result的下标
            _result[power] = int(_num / sys ** power)  # 赋值
            _num -= sys ** power * int(_num / sys ** power)  # 自减 dnumber
            if _num > 0:
                _num, _result = _recursion(_num, _result)
            return _num, _result

        def _get_c_type(_sys):
            """ _get_c_type by sys """
            type_mapping = [
                {"max": 255, "c_type": "B"},
                {"max": 65535, "c_type": "H"},
                {"max": 4294967295, "c_type": "I"},
            ]
            for _mapping in type_mapping:
                if _sys < _mapping["max"]:
                    return _mapping["c_type"]
            else:
                raise Exception(f"sys is out of range({type_mapping[-1]['max']})")

        c_type = _get_c_type(sys)  # 获取C类型
        # 创建值为0且索引值足够的结果列表 由array代替list以提升执行效率
        result = array(c_type, (0 for _ in range(0, int(math.log(num, sys)) + 1)))
        num, result = _recursion(num, result.tolist())  # 递归
        result = result[::-1]
        return result


if __name__ == "__main__":
    print("===============================================")  # 功能1: 获取 python 对象信息, 应用场景: 游戏存档读写
    # 创建原数据
    test_1 = {"obj_name": "name", "list_data": [1, 2, 3, 4, {"d": 1}], "dict_data": {"a": 1, "b": 2}, "obj_data": None}
    test_2 = copy.deepcopy(test_1)
    test_1["obj_data"] = test_2

    # 设置保护属性 展示数据
    o = RStruct()
    o.load(d_data=test_1, protection=["dict_data"])
    # print(o.__dict__)
    o.detail()

    # 不设置保护属性 展示数据
    o = RStruct()
    o.load(d_data=test_1)
    # print(o.__dict__)
    o.detail()

    print("===============================================")  # 功能2: 获取 python 对象信息
    data = Image.open(r"E:\1.png").convert("RGB")  # 图片的对象
    dump(data, _print=True)

    print("===============================================")  # 功能3: 创建无限循环的生成器, 应用场景: 游戏动画循环
    generator = RGenerator((0, 1, 2, 3, 4))  # 创建生成器
    for _ in range(100):
        print(generator.next())

    print("===============================================")  # 功能4: 将十进制的数值转为指定进制
    test = calcsys(999999999, 32)  # 将十进制 999999999 转为 32 进制
    print(test)


