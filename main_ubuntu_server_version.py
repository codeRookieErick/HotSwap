import sys

from MyModules import ModuleAutoLoader, ModulesRunner

ipc = Worker()
progressBar = Control("MyIpcProgressBar", "progressBar")
ipc.addControl(progressBar)

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