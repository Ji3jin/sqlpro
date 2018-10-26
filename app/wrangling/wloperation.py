# *-* encoding=utf-8 *-*
from .wgmodel import OperationType
from .ruleloader import rule_loader
from .wgmodel import get_op_type, get_axis
import json


class WlOperation(object):
    def __init__(self, attr_name, is_callable=False, param_num=0, op_type=None, user_input=False, op_param=None):
        self.attr_name = attr_name
        self.op_param = [] if op_param is None else op_param
        self.is_callable = is_callable
        self.param_num = param_num
        self.op_type = op_type
        self.desc = None
        self.user_input = user_input

    def op_param_append(self, param):
        self.op_param.append(param)

    def get_checked_param(self):
        # check param with attr_name
        assert len(self.op_param) == self.param_num
        return tuple(self.op_param)

    def __str__(self):
        return self.attr_name


def get_recommend_operation(df, x_index, y_index):
    recommend_op = []
    op_type = get_op_type(x_index, y_index)
    if op_type == OperationType.DEFAULT:
        print("当前选择的操作对象索引为({0},{1})，该对象为表级操作".format(x_index, y_index))
        for key, value in rule_loader.get_rules("base_table_op"):
            info = value.split("|")
            wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                op_type=op_type.value,
                                user_input=json.loads(info[3].lower()))
            wl_op.desc = info[-1]
            recommend_op.append(wl_op.__dict__)
    elif op_type == OperationType.ROW:
        print("当前选择的操作对象索引为({0},{1})，该对象为行级操作".format(x_index, y_index))
        for key, value in rule_loader.get_rules("base_row_op"):
            info = value.split("|")
            wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                op_type=op_type.value,
                                user_input=json.loads(info[3].lower()))
            wl_op.desc = info[-1]
            if int(info[2]) == 1 and not json.loads(info[3].lower()):
                wl_op.op_param_append(x_index - 1)
            recommend_op.append(wl_op.__dict__)
    elif op_type == OperationType.COLUMN:
        print("当前选择的操作对象索引为({0},{1})，该对象为列级操作".format(x_index, y_index))
        for key, value in rule_loader.get_rules("base_column_op"):
            info = value.split("|")
            wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                op_type=op_type.value,
                                user_input=json.loads(info[3].lower()))
            wl_op.desc = info[-1]
            if int(info[2]) == 1 and not json.loads(info[3].lower()):
                # set column index
                wl_op.op_param_append(df.columns[y_index - 1])
            recommend_op.append(wl_op.__dict__)
    else:
        print("当前选择的操作对象索引为({0},{1})，该对象为单元格级操作，暂无推荐操作".format(x_index, y_index))
        pass
    return recommend_op
