#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File  : pengine.py
# Author: jixin
# Date  : 18-10-24
from sqlalchemy.engine import create_engine
import pandas as pd
import os
from config import config
import threading
import uuid
from ..core.redisobj import redis_pool
from cachetools import TTLCache
import hashlib

query_cache = TTLCache(maxsize=256, ttl=300)


def get_md5(sql):
    if isinstance(sql, str):
        sql = sql.encode("utf-8")
    md = hashlib.md5()
    md.update(sql)
    return md.hexdigest()


class PagedDataFrame(object):
    def __init__(self, sql, iter):
        self.cached_index = 0
        self.iter = iter
        self.data = None
        self.sql = sql
        self.uid = uuid.uuid4().hex
        self.lock = threading.Lock()

    def get_page(self, page_index=1):
        self.lock.acquire()
        if page_index > self.cached_index:
            for i in range(self.cached_index, page_index):
                try:
                    self._get_next_page()
                except StopIteration:
                    self.data = None
                    break
        else:
            self._get_cached_page(page_index)
        self.lock.release()
        return self.data

    def _get_next_page(self):
        r = redis_pool.get_instance()
        self.data = self.iter.__next__()
        r.rpush(self.uid, self.data.to_json(orient='split'))
        self.cached_index += 1

    def _get_cached_page(self, index):
        r = redis_pool.get_instance()
        cached_data = r.lindex(self.uid, index=index - 1)
        self.data = pd.read_json(cached_data, orient='split')

    def __del__(self):
        r = redis_pool.get_instance()
        if r.exists(self.uid):
            r.delete(self.uid)


class QueryEngine(object):
    def __init__(self):
        config_name = os.getenv('FLASK_CONFIG') or 'default'
        presto_uri = config[config_name].PRESTO_URI
        self.engine = create_engine(presto_uri)

    def show_catalogs(self):
        df = pd.read_sql("show catalogs", self.engine)
        return df

    def show_schemas(self, catalog):
        sql = "show schemas from {0}".format(catalog)
        key = get_md5("{0}_treeview".format(sql))
        if query_cache.__contains__(key):
            return query_cache[key]
        else:
            df = pd.read_sql(sql, self.engine)
            query_cache[key] = df
            return df

    def show_tables(self, catalog, schema):
        sql = "show tables from {0}.{1}".format(catalog, schema)
        key = get_md5("{0}_treeview".format(sql))
        if query_cache.__contains__(key):
            return query_cache[key]
        else:
            df = pd.read_sql(sql, self.engine)
            query_cache[key] = df
            return df

    def show_columns(self, catalog, schema, table):
        sql = "show columns from {0}.{1}.{2}".format(catalog, schema,table)
        key = get_md5("{0}_treeview".format(sql))
        if query_cache.__contains__(key):
            return query_cache[key]
        else:
            df = pd.read_sql(sql, self.engine)
            query_cache[key] = df
            return df

    def query(self, sql, size):
        df = pd.read_sql(sql, self.engine, chunksize=size)
        paged_df = PagedDataFrame(sql, df)
        query_cache[get_md5(sql)] = paged_df
        return paged_df

    def query_all(self, sql):
        df = pd.read_sql(sql, self.engine)
        return df


query_engine = QueryEngine()
