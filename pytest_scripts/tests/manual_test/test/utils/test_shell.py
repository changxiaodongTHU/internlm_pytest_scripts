#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   Lijialun

@License :   (C) Copyright 2022-2023, PJLAB 

@Contact :   lijialun@pjlab.org.cn

@Software:   PyCharm

@File    :   test_shell.py

@Time    :   2023/4/24 下午4:12

@Desc    :
"""
from framework.utils.shell import Shell


class TestShell:
    def test_shell_exec(self):
        """
        only on linux
        """
        sh = Shell()
        status_code, out = sh.exec_cmd("echo hello world")
        assert status_code == 0
        assert out == "hello world\n"

    def test_shell_exec_with_env(self):
        """
        only on linux
        """
        sh = Shell({"HELLO": "WORLD"})
        status_code, out = sh.exec_cmd("echo $HELLO")
        assert status_code == 0
        assert out == "WORLD\n"

    def test_shell_exec_with_param_env(self):
        """
        only on linux
        """
        sh = Shell()
        status_code, out = sh.exec_cmd("echo $HELLO", {"HELLO": "WORLD"})
        assert status_code == 0
        assert out == "WORLD\n"
