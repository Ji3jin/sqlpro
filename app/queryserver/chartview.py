#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : chartview.py
# Author: jixin
# Date  : 18-10-25

class ChartView(object):
    @staticmethod
    def fill_data(chart, df):
        xaxis = chart.xaxis
        yaxis = chart.yaxis.split(',')

        data = {}
        data[xaxis] = df[xaxis].tolist()
        for item in yaxis:
            data[item] = df[item].tolist()

        return {'data': data, 'xaxis': xaxis, 'yaxis': yaxis, 'template_type': chart.template_type.value,
                'name': chart.chart_name}
