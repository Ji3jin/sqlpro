#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : test.py.py
# Author: jixin
# Date  : 18-10-26
# -*- coding=utf-8 -*-
import os
import re
import warnings
import datetime

warnings.filterwarnings("ignore")

# src Database config
srcMysqlConfig_jellyfish_server = {
    'host': 'MysqlHost',
    # 'host': 'MysqlHost',
    'user': 'MysqlUser',
    'passwd': 'MysqlPass',
    'port': 50506,
    'db': 'jellyfish_server'
}

def dateRange(beginDate, endDate):
    dates = []
    dt = datetime.datetime.strptime(beginDate, "%Y-%m-%d")
    date = beginDate[:]
    while date <= endDate:
        dates.append(date)
        dt = dt + datetime.timedelta(1)
        date = dt.strftime("%Y-%m-%d")
    return dates

def getSrcMysqlConfig(srcMysql_config):
    srcMysql_config = srcMysql_config
    return srcMysql_config['host'], srcMysql_config['port'], srcMysql_config['user'], srcMysql_config['passwd'], srcMysql_config['db']

def getMysqlTabScript(srcMysql_config, src_tabName, tabType, whereCondition):
    # Parameter initialization
    host = getSrcMysqlConfig(srcMysql_config)[0]
    port = getSrcMysqlConfig(srcMysql_config)[1]
    user = getSrcMysqlConfig(srcMysql_config)[2]
    passwd = getSrcMysqlConfig(srcMysql_config)[3]
    db = getSrcMysqlConfig(srcMysql_config)[4]

    if tabType == 'single':
        src_postfix = ''
    elif 'submeter' in tabType:
        src_postfix = '_0'

    srcTabStructure = os.popen("""source /etc/profile; \
            /usr/bin/mysql -h{host} -P{port} -u{user} -p{passwd} -D{db} \
            -N -e"set names utf8; \
            select a2.column_name,case when a2.data_type like '%int' then 'bigint' else 'string' end data_type
            from information_schema.TABLES a1
            left join information_schema.columns a2 on a1.TABLE_SCHEMA=a2.TABLE_SCHEMA and a1.TABLE_NAME=a2.TABLE_NAME
            where a1.TABLE_SCHEMA='{db}' and a1.table_name ='{src_tabName}{src_postfix}'
            order by a2.ORDINAL_POSITION;" \
            """ .format(host=host, port=port, user=user, passwd=passwd, db=db, src_tabName=src_tabName, src_postfix=src_postfix)).readlines();

    srcTabCol_list = []
    for stcList in srcTabStructure:
        stc = re.split('\t', stcList.replace('\n', ''))
        srcTabCol_list.append(stc)
    TabCreateScript = 'use ods;\ndrop table if exists {db}_{src_tabName};\ncreate table {db}_{src_tabName}(\n'.format(src_tabName=src_tabName, db=db)
    TabSelectScriptHalf = 'select '
    for srcColType in srcTabCol_list:
        TabSelectScriptHalf = TabSelectScriptHalf + '' + srcColType[0] + ','
        TabCreateScript = TabCreateScript + '\`' + srcColType[0] + '\`' + ' ' + srcColType[1] + ',\n'

    TabSelectScriptHalf = TabSelectScriptHalf[:-1]
    TabCreateScript = TabCreateScript[:-2] + ") partitioned by (\`pt_day\` string) row format delimited fields terminated by '\t' lines terminated by '\n' location 'hdfs://emr-cluster/user/hive/warehouse/ods.db/{db}_{src_tabName}';".format(src_tabName=src_tabName, db=db)

    # get submeter table count
    if tabType == 'single':
        submeter_cnt = 1
    elif 'submeter' in tabType:
        submeter_cnt = int(str(tabType).replace('submeter-', ''))

    # partition table data load
    TabSelectScript=''
    for submeterPlus in range(0, submeter_cnt, 1):
        # get submeter table postfix
        if tabType == 'single':
            submeterPostfix = ''
        elif 'submeter' in tabType:
            submeterPostfix = '_' + str(submeterPlus)

        TabSelectScriptSingle = TabSelectScriptHalf + " from {src_tabName}{submeterPostfix} where {whereCondition}\nunion all\n".format(src_tabName=src_tabName, submeterPostfix=submeterPostfix, whereCondition=whereCondition)
        TabSelectScript = TabSelectScript + TabSelectScriptSingle
    TabSelectScript = TabSelectScript[:-11] + " and \$CONDITIONS;"

    return TabCreateScript, TabSelectScript

def HiveCreateTab(srcMysql_config, src_tabName, tabType):
    TabCreateScript = getMysqlTabScript(srcMysql_config, src_tabName, tabType, whereCondition="")[0]
    os.system("""/usr/lib/hive-current/bin/hive -e "{TabCreateScript}" """.format(TabCreateScript=TabCreateScript))

def mysqlData2Hive(srcMysql_config, src_tabName, tabType, runDay, whereCondition):
    # Parameter initialization
    host = getSrcMysqlConfig(srcMysql_config)[0]
    port = getSrcMysqlConfig(srcMysql_config)[1]
    user = getSrcMysqlConfig(srcMysql_config)[2]
    passwd = getSrcMysqlConfig(srcMysql_config)[3]
    db = getSrcMysqlConfig(srcMysql_config)[4]

    TabSelectScript = getMysqlTabScript(srcMysql_config, src_tabName, tabType, whereCondition)[1]

    # add partitions
    os.system("""source /etc/profile; \
            /usr/lib/hive-current/bin/hive -e "
            use ods;
            alter table {db}_{src_tabName} drop if exists partition (pt_day='{runDay}'); \
            alter table {db}_{src_tabName} add partition (pt_day='{runDay}');" \
            """.format(host=host, port=port, user=user, passwd=passwd, db=db, src_tabName=src_tabName, runDay=runDay))

    # partition table data load
    os.system("""source /etc/profile; \
            sqoop import \
            --connect jdbc:mysql://{host}:{port}/{db}?zeroDateTimeBehavior=convertToNull \
            --username {user} \
            --password {passwd} \
            --query "{TabSelectScript}" \
            --target-dir hdfs://emr-cluster/user/hive/warehouse/ods.db/{db}_{src_tabName}/pt_day={runDay} \
            --delete-target-dir \
            --fields-terminated-by '\t' \
            --lines-terminated-by '\n' \
            --num-mappers 1 \
            --compress \
            --compression-codec org.apache.hadoop.io.compress.SnappyCodec \
            --direct \
            --driver com.mysql.jdbc.Driver -m 8 \
            """.format(host=host, port=port, user=user, passwd=passwd, db=db, src_tabName=src_tabName, runDay=runDay, TabSelectScript=TabSelectScript))


# Batch Test
HiveCreateTab(srcMysql_config=srcMysqlConfig_jellyfish_server, src_tabName='live_history_status', tabType='submeter-256')
HiveCreateTab(srcMysql_config=srcMysqlConfig_jellyfish_server, src_tabName='big_fans_detail', tabType='single')
for runDay in dateRange(beginDate='2018-03-26', endDate='2018-03-28'):
    mysqlData2Hive(srcMysql_config=srcMysqlConfig_jellyfish_server, src_tabName='live_history_status', tabType='submeter-256', runDay=runDay, whereCondition="substr(updated_time, 1, 10) = '{runDay}'".format(runDay=runDay))
    mysqlData2Hive(srcMysql_config=srcMysqlConfig_jellyfish_server, src_tabName='big_fans_detail', tabType='single', runDay=runDay, whereCondition="point=20000")
