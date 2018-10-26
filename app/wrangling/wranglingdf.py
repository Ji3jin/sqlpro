# *-* encoding=utf-8 *-*
from .wgmodel import *
from .wloperation import WlOperation
import json
from .ruleloader import rule_loader


class WrangLingDF():
    def __init__(self):
        self._dtypes = {}
        self._extract_record = []

    @property
    def extract_record(self):
        return self._extract_record

    @property
    def dtypes(self):
        return self._dtypes

    def get_wl_df_dtypes(self):
        for key, value in self._dtypes.items():
            print("数据列{0},数据类型为{1},数据质量为{2}%".format(key, value[0], value[1] * 100))

    # 检测数据类型，并且统计数据质量（全局）
    def pre_deal_data(self, df):
        dtypes = df.dtypes
        # pandas读取数据本身会进行一次检测，如果有空值或者异常值会检测成object
        # 如果正常值会检测出数据类型，此时数据质量是百分百
        for item in list(dtypes.index):
            dtype = str(dtypes[item])
            # 检测所有为Object的是否为基础类型，基础类型为num，float和string
            # 如果不满足num和float的正则则为string（表现为object）
            if dtype == 'object':
                # CHECK_TYPE is num and float
                for check_type in CHECK_TYPE:
                    regex = rule_loader.get_option(check_type[0].value, 'regex')
                    right_value = df[item].str.contains(regex, regex=True)
                    q = round(float(right_value[right_value == True].count()) / float(df[item].shape[0]), 2)
                    if q > 0.75:
                        self._dtypes[item] = (check_type[1], q, check_type[0].value)
                        break
            # dtype为object或者为数据质量百分百的类型。如果为Object则认定Nan为异常值，统计数据质量
            q = round(float(df[item].count()) / float(df[item].shape[0]), 2)
            self._dtypes[item] = (dtype, q, DataType.STRING.value)
        self.get_wl_df_dtypes()

    # 获取处理后的结果集
    def extract_dataframe(self, df, wl_operation):
        # 处理数据
        if wl_operation:
            extract_func = getattr(df, wl_operation.attr_name, wl_operation.attr_name)
            if wl_operation.is_callable:
                if wl_operation.op_type == OperationType.COLUMN.value and get_axis(wl_operation.attr_name):
                    df = extract_func(*wl_operation.get_checked_param(), axis=1)
                else:
                    df = extract_func(*wl_operation.get_checked_param())
            else:
                df = extract_func
        try:
            self.pre_deal_data(df)
            self._extract_record.append(wl_operation)
        except:
            pass
        return df

    # 撤销操作
    def undo_dataframe(self, df):
        self._extract_record.pop(-1)
        return self.redo_dataframe(df)

    def redo_dataframe(self, df):
        for item in self._extract_record:
            if item:
                extract_func = getattr(df, item.attr_name, item.attr_name)
                if item.is_callable:
                    if item.op_type == OperationType.COLUMN and get_axis(item.attr_name):
                        result_df = extract_func(*item.get_checked_param(), axis=1)
                    else:
                        result_df = extract_func(*item.get_checked_param())
                else:
                    result_df = extract_func
                df = result_df
        return df
