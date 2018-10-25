# *-* encoding=utf-8 *-*
from .wgmodel import OperationType


class WlOperation(object):
    def __init__(self, attr_name, is_callable=False, param_num=0, op_type=None, user_input=False):
        self._attr_name = attr_name
        self._op_param = []
        self._is_callable = is_callable
        self._param_num = param_num
        self._desc = None
        self._op_type = op_type

    @property
    def op_type(self):
        return self._op_type

    @op_type.setter
    def op_type(self, op_type):
        self._op_type = op_type

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, desc):
        self._desc = desc

    @property
    def param_num(self):
        return self._param_num

    @param_num.setter
    def param_num(self, param_num):
        self._param_num = param_num

    @property
    def attr_name(self):
        return self._attr_name

    @attr_name.setter
    def attr_name(self, attr_name):
        self._attr_name = attr_name

    @property
    def is_callable(self):
        return self._is_callable

    @is_callable.setter
    def is_callable(self, is_callable):
        self._is_callable = is_callable

    @property
    def op_param(self):
        return tuple(self._op_param)

    def op_param_append(self, param):
        self._op_param.append(param)

    def get_checked_param(self):
        # check param with attr_name
        assert len(self._op_param) == self._param_num
        return tuple(self._op_param)

    def __str__(self):
        return self._attr_name + "--|--" + self._desc
