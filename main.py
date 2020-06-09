import sys
sys.path.insert(1, "D:\\bots\\ScriptsManager\\lib\\python")

from MyModules import ModuleAutoLoader, ModulesRunner
from MyIpc import Worker, Control

ipc = Worker()
progressBar = Control("MyIpcProgressBar", "progressBar")
ipc.addControl(progressBar)

def methodCalled(name, count, size):
    progressBar.setProperty("Title", name)
    progressBar.setProperty("Maximun", size)
    progressBar.setProperty("Value", count)

def onPrint(data):
    ipc.print(data)

with ModulesRunner('workers', ['main']) as k:
    k.onMethodCalled = methodCalled
    k.onPrint = onPrint
    k.mainEventLoop()