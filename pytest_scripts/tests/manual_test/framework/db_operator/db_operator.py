#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   changxiaodong

@License :   (C) Copyright 2023, PJLAB 

@Contact :   changxiaodong@pjlab.org.cn

@Software:   PyCharm

@File    :   db_operator.py

@Time    :   2023/7/31

@Desc    :
"""
import yaml
import pymongo

default_mongodb_config = {
    "MONGO_URL": "10.140.52.25",
    "MONGO_USER": "root",
    "MONGO_PASSWD": "password"
}


class Operator:
    def __init__(self, config_path: str = None):
        self.client = None
        self.db = None
        self.collection = None
        self.config = default_mongodb_config
        config = {}
        if config_path:
            with open(config_path, "r") as f:
                config = yaml.load(f.read(), yaml.FullLoader)
        for i in config:
            if i not in self.config:
                raise KeyError("Config key error, please check your mongodb config")
            self.config[i] = config[i]
        self.init_client()

    def init_client(self):
        self.client = pymongo.MongoClient(
            "mongodb://" + self.config['MONGO_USER'] +
            ":" + self.config['MONGO_PASSWD'] + "@" +
            self.config['MONGO_URL'] + ":27017/")

    def set_db(self, db_name: str) -> None:
        self.db = db_name

    def set_collection(self, collection_name: str) -> None:
        self.collection = collection_name

    def show_dbs(self) -> list:
        return self.client.list_database_names()

    def close_client(self):
        self.client.close()
        self.client = None
