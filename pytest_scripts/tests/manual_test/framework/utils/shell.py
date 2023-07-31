#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@Author  :   changxiaodong

@License :   (C) Copyright 2022-2023, PJLAB 

@Contact :   changxiaodong@pjlab.org.cn

@Software:   PyCharm

@File    :   shell.py

@Time    :   2023/4/24 下午4:02

@Desc    :
"""
import subprocess

from framework.utils.common import Common


class Shell(Common):
    """
    Linux only
    """

    def __init__(self, env_var: dict = None, virtual_env: str = None, conda_env: str = None):
        super().__init__()
        self.env_var = env_var
        self.virtual_env = virtual_env
        self.conda_env = conda_env

    def _handle_command(self, command: str, environment: dict):
        if self.env_var:
            command = self._make_env_command(self.env_var) + ";" + command
        if environment:
            command = self._make_env_command(environment) + ";" + command
        if self.virtual_env:
            command = "source " + self.virtual_env + "/bin/activate;" + command
        if not self.virtual_env and self.conda_env:
            command = "conda activate " + self.virtual_env + ";" + command
        return command

    def exec_cmd(self, command: str, environment: dict = None) -> tuple:
        out, exit_code = '', -1
        if not command:
            return exit_code, out
        command = self._handle_command(command, environment)
        res = subprocess.run([command], capture_output=True, shell=True)
        exit_code = res.returncode
        out = res.stdout.decode("utf-8")
        return exit_code, out
