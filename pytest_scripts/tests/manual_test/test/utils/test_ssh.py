#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   Lijialun

@License :   (C) Copyright 2022-2023, PJLAB 

@Contact :   lijialun@pjlab.org.cn

@Software:   PyCharm

@File    :   test_ssh.py

@Time    :   2023/4/24 下午3:40

@Desc    :
"""
from framework.utils.ssh import SSH


class TestSSH:
    def test_ssh_login_and_exec_cmd(self):
        # jetson's ip
        with SSH("10.1.83.108", 22, 'apx103', password='0000') as client:
            client.get_client()
            status_code, out = client.exec_command("echo hello world")
            assert status_code == 0
            assert out == "hello world\r\n"

    def test_ssh_login_and_exec_cmd_with_env(self):
        # jetson's ip
        with SSH("10.1.83.108", 22, 'apx103', password='0000') as client:
            client.get_client()
            status_code, out = client.exec_command("echo $HELLO", {"HELLO": "WORLD"})
            assert status_code == 0
            assert out == "WORLD\r\n"
