#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   changxiaodong

@License :   (C) Copyright 2023, PJLAB 

@Contact :   changxiaodong@pjlab.org.cn

@Software:   PyCharm

@File    :   common.py

@Time    :   2023/4/24 下午4:26

@Desc    :
"""
from io import StringIO
from uuid import uuid4


class Common:
    def __init__(self):
        pass

    @staticmethod
    def _make_env_command(environment):
        """
        make env set str
        :param environment: dict
        :return:
        """
        if not environment:
            return None
        str_envs = []
        for k, v in environment.items():
            k = k.replace('-', '_')
            if isinstance(v, str):
                v = v.replace("'", "'\"'\"'")
            str_envs.append(f"{k}='{v}'")
        str_envs = ' '.join(str_envs)
        return f'export {str_envs}'
