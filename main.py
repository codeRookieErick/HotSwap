import sys

from modules.modules_autoloader import ModuleAutoLoader
from modules.modules_runner import ModulesRunner

def methodCalled(name, count, size):
    print(f"Title: {name}")
    print(f"Maximun: {size}")
    print(f"Value {count}")

def onPrint(data):
    print(data)

with ModulesRunner('workers', ['main']) as k:
    k.onMethodCalled = methodCalled
    k.onPrint = onPrint
    k.mainEventLoop()