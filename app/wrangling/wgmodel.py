# *-* encoding=utf-8 *-*
from enum import Enum, unique


@unique
class DataType(Enum):
    NUM = 'data_type_num'
    FLOAT = 'data_type_float'
    STRING = 'data_type_string'
    DATETIME = 'data_type_datetime'


@unique
class OperationType(Enum):
    ROW = 'row'
    COLUMN = 'column'
    CELL = 'cell'
    DEFAULT = 'table'


def get_op_type(x_index, y_index):
    if x_index == 0 and y_index == 0:
        return OperationType.DEFAULT
    elif x_index == 0:
        return OperationType.COLUMN
    elif y_index == 0:
        return OperationType.ROW
    else:
        return OperationType.CELL


def get_axis(attr_name):
    if attr_name in AXIS_ATTR:
        return True


CHECK_TYPE = ((DataType.NUM, 'int64'), (DataType.FLOAT, 'float64'))

AXIS_ATTR = ("drop", "dropna")
