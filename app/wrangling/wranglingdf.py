# *-* encoding=utf-8 *-*
from .wgmodel import *
from .wloperation import WlOperation
import json


class WrangLingDF():
    def __init__(self, rule_loader, df):
        self._rule_loader = rule_loader
        self._dataframe = df
        self._dtypes = {}
        self.pre_deal_data()
        self._wl_operation = None
        self._extract_record = []

    @property
    def extract_record(self):
        return self._extract_record

    @property
    def dataframe(self):
        return self._dataframe

    @dataframe.setter
    def dataframe(self, df):
        self._dataframe = df

    @property
    def wl_operation(self):
        return self._wl_operation

    @wl_operation.setter
    def wl_operation(self, wl_operation):
        self._wl_operation = wl_operation

    @property
    def dtypes(self):
        return self._dtypes

    def get_wl_df_dtypes(self):
        for key, value in self._dtypes.items():
            print ("数据列{0},数据类型为{1},数据质量为{2}%".format(key, value[0], value[1] * 100))

    # 检测数据类型，并且统计数据质量（全局）
    def pre_deal_data(self):
        dtypes = self._dataframe.dtypes
        # pandas读取数据本身会进行一次检测，如果有空值或者异常值会检测成object
        # 如果正常值会检测出数据类型，此时数据质量是百分百
        for item in list(dtypes.index):
            dtype = str(dtypes[item])
            # 检测所有为Object的是否为基础类型，基础类型为num，float和string
            # 如果不满足num和float的正则则为string（表现为object）
            if dtype == 'object':
                # CHECK_TYPE is num and float
                for check_type in CHECK_TYPE:
                    regex = self._rule_loader.get_option(check_type[0].value, 'regex')
                    q = self.check_dtype(item, regex)
                    if q > 0.75:
                        self._dtypes[item] = (check_type[1], q, check_type[0].value)
                        break
            # dtype为object或者为数据质量百分百的类型。如果为Object则认定Nan为异常值，统计数据质量
            q = round(float(self._dataframe[item].count()) / float(self._dataframe[item].shape[0]), 2)
            self._dtypes[item] = (dtype, q, DataType.STRING.value)
        self.get_wl_df_dtypes()

    def check_dtype(self, item, regex):
        right_value = self._dataframe[item].str.contains(regex, regex=True)
        q = round(float(right_value[right_value == True].count()) / float(self._dataframe[item].shape[0]), 2)
        return q

    # 关联某列的抽象模型，关联后需重新统计该列的数据质量
    def relate_deal_module(self, col_index, data_type):
        regex = self._rule_loader.get_option(data_type, 'regex')
        dtype = self._rule_loader.get_option(data_type, 'dtype')
        q = self.check_dtype(col_index, regex)
        self._dtypes[col_index] = (dtype, q, data_type)

    # 获取处理后的结果集
    def extract_dataframe(self, wl_operation):
        # 处理数据
        self.wl_operation = wl_operation
        extract_func = getattr(self._dataframe, wl_operation.attr_name, wl_operation.attr_name)
        if wl_operation.is_callable:
            if wl_operation.op_type == OperationType.COLUMN and get_axis(wl_operation.attr_name):
                result_df = extract_func(*wl_operation.get_checked_param(), axis=1)
            else:
                result_df = extract_func(*wl_operation.get_checked_param())
        else:
            result_df = extract_func

        self._dataframe = result_df
        try:
            self.pre_deal_data()
        except:
            pass
        self._extract_record.append({"wl_op": wl_operation, "wl_df": result_df})

    # 撤销操作
    def undo_dataframe(self):
        last = self._extract_record[-1]
        self._dataframe = last.get("wl_df")
        self.wl_operation = last.get("wl_op")
        self.pre_deal_data()
        self._extract_record.remove(last)

    def get_code(self):
        for item in self._extract_record:
            print(item.get("wl_op"))

    # 获取推荐操作
    def get_recommend_operation(self, op_index):
        recommend_op = []
        op_type = get_op_type(op_index)
        if op_type == OperationType.DEFAULT:
            print ("当前选择的操作对象索引为({0},{1})，该对象为表级操作".format(op_index[0], op_index[1]))
            for key, value in self._rule_loader.get_rules("base_table_op"):
                info = value.split("|")
                wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                    op_type=op_type,
                                    user_input=json.loads(info[3].lower()))
                wl_op.desc = info[-1]
                recommend_op.append(wl_op)
        elif op_type == OperationType.ROW:
            print ("当前选择的操作对象索引为({0},{1})，该对象为行级操作".format(op_index[0], op_index[1]))
            for key, value in self._rule_loader.get_rules("base_row_op"):
                info = value.split("|")
                wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                    op_type=op_type,
                                    user_input=json.loads(info[3].lower()))
                wl_op.desc = info[-1]
                if int(info[2]) == 1 and not json.loads(info[3].lower()):
                    wl_op.op_param_append(self._dataframe.index[op_index[0] - 1])
                recommend_op.append(wl_op)
        elif op_type == OperationType.COLUMN:
            print ("当前选择的操作对象索引为({0},{1})，该对象为列级操作".format(op_index[0], op_index[1]))
            for key, value in self._rule_loader.get_rules("base_column_op"):
                info = value.split("|")
                wl_op = WlOperation(info[0], is_callable=json.loads(info[1].lower()), param_num=int(info[2]),
                                    op_type=op_type,
                                    user_input=json.loads(info[3].lower()))
                wl_op.desc = info[-1]
                if int(info[2]) == 1 and not json.loads(info[3].lower()):
                    # set column index
                    wl_op.op_param_append(self._dataframe.columns[op_index[1] - 1])
                recommend_op.append(wl_op)
        else:
            print ("当前选择的操作对象索引为({0},{1})，该对象为单元格级操作，暂无推荐操作".format(op_index[0], op_index[1]))
            pass
        return recommend_op
