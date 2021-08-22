import subprocess
import sys
import logging

from abc import ABC, abstractmethod


class Executer(ABC):
    """
    Wrapper for the execution functionality in MTF that deals with the platfrom specific
    stuff.
    """

    _execute_script = None
    _execute_command = None

    @abstractmethod
    def execute(self, arg: str):
        pass


class WinExecuter(Executer):
    """
    Execution rules for windows platform
    """

    def __init__(self, shell_type: str = "powershell"):
        if shell_type == "powershell":
            self._execute_script = "mimir/frontend/terminal/executable/win/runVLC.ps1"
            self._execute_command = "powershell.exe"
        else:
            raise NotImplementedError("Shell type %s not defined" % shell_type)

    def execute(self, arg: str):
        execute_script = f"{self._execute_script} {arg}"
        logging.debug(execute_script)
        subprocess.Popen([self._execute_command, execute_script], stdout=sys.stdout)


class LinuxExecuter(Executer):
    """
    Execution rules for linux platform
    """

    def __init__(self, shell_type: str = "bash"):
        if shell_type == "bash":
            self._execute_script = "mimir/frontend/terminal/executable/linux/runVLC.sh"
        else:
            raise NotImplementedError("Shell type %s not defined" % shell_type)

    def execute(self, arg: str):
        execute_script = f"{self._execute_script} {arg}"
        logging.debug(execute_script)
        subprocess.Popen([execute_script], stdout=sys.stdout)


class MacOSExecuter(Executer):
    def __init__(self, shell_type: str = "bash"):
        if shell_type == "bash":
            self._execute_script = "mimir/frontend/terminal/executable/macOS/runVLC.sh"
        else:
            raise NotImplementedError("Shell type %s not defined" % shell_type)

    def execute(self, arg: str):
        execute_script = f"{self._execute_script} {arg}"
        logging.debug(execute_script)
        subprocess.Popen([execute_script], stdout=sys.stdout)
