#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   changxiaodong

@License :   (C) Copyright 2023, PJLAB 

@Contact :   changxiaodong@pjlab.org.cn

@Software:   PyCharm

@File    :   uploader.py

@Time    :   2023/8/1

@Desc    :
"""
from tests.manual_test.framework.db_operator.db_operator import Operator


class Uploader(Operator):
    def __init__(self, config_path: str = None):
        super().__init__(config_path)

    def upload(self, data: dict) -> None:
        if not self.db and not self.collection:
            raise RuntimeError("Please set database and collections first.")
        collection = self.client[self.db][self.collection]
        collection.insert_one(data)

    def update(self, update_filter: dict, data: dict):
        if not self.db and not self.collection:
            raise RuntimeError("Please set database and collections first.")
        collection = self.client[self.db][self.collection]
        collection.update_one(update_filter, {"$set": data})
