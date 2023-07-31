#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   Lijialun

@License :   (C) Copyright 2022-2023, PJLAB 

@Contact :   lijialun@pjlab.org.cn

@Software:   PyCharm

@File    :   test_uploader.py

@Time    :   2023/4/24 上午10:52

@Desc    :
"""
from framework.db_operator.uploader import Uploader


class TestDataUploader:
    def test_data_upload(self):
        uploader = Uploader()

        uploader.set_db('test')

        result = {'test': 'test'}
        db_name = 'test'
        collection_name = 'test'

        uploader.set_db(db_name)
        uploader.set_collection(collection_name)

        uploader.upload(result)

        uploader.client[uploader.db][uploader.collection].find_one({'test': 'test'})
        uploader.client[uploader.db][uploader.collection].delete_many({'test': 'test'})

        uploader.close_client()

    def test_data_update(self):
        uploader = Uploader()

        uploader.set_db('test')

        result = {'test': 'test'}
        db_name = 'test'
        collection_name = 'test'

        uploader.set_db(db_name)
        uploader.set_collection(collection_name)

        uploader.upload(result)

        uploader.update({'test': 'test'}, {'test': 'train'})
        uploader.client[uploader.db][uploader.collection].delete_many({'test': 'train'})

        uploader.close_client()

