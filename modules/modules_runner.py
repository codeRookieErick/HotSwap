import time
from threading import Lock

from .modules_autoloader import ModuleAutoLoader

class ModulesRunner:
    def __init__(self, path, methodsToFind, onPrint = None):
        self.onPrint = onPrint or (lambda x: print(f'Fromhere: {x}'))
        self.autoLoader = ModuleAutoLoader(path)
        self.methodsToFind = methodsToFind
        self.methods = {}
        self.autoLoader.onModuleAdded = (lambda path, module: self.module_added(path, module))
        self.autoLoader.onModuleDeleted = (lambda path, module: self.module_removed(path, module))
        self.autoLoader.onModuleLoaded = (lambda path, module: self.module_updated(path, module))
        self.autoLoader.onModuleError = (lambda path, module: self.module_error(path))
        self.onMethodCalled = (lambda name, index, count: None)
        self.mutex = Lock()

    def __enter__(self):
        return self

    def module_added(self, path, module):
        self.onPrint(f'Module added : {path}')
        pass

    def module_updated(self, path, module):
        self.mutex.acquire()
        self.onPrint(f'Module updated : {path}')
        module.print = self.onPrint
        methods = [(getattr(module, i), i) for i in dir(module) if i in self.methodsToFind]
        methods = [i for i in methods if callable(i[0])]
        if(len(methods) > 0):
            self.onPrint(' :: Method: {0}.{1}'.format(path, methods[0][1]))
            self.methods[path] = methods[0][0]
        else:
            self.onPrint(f' :: Not suitable method found in {path} : requested {self.methodsToFind}')
        self.mutex.release()

    def module_removed(self, path, module):
        if path in self.methods.keys():
            self.onPrint(f'Module deleted : {path}')
            del self.methods[path]
        pass
    
    def module_error(self, path):
        self.onPrint(f'Error on Module : {path}')
        pass

    def mainEventLoop(self):
        try:
            self.autoLoader.start()
            while True:
                time.sleep(1)
                try:
                    self.mutex.acquire()
                    modules = [i for i in self.methods.keys()]
                    count = 0
                    for i in modules:
                        count += 1
                        self.onMethodCalled(i, count, len(modules))
                        self.methods[i]()
                finally:
                    self.mutex.release()
        except Exception as e:
            print(e)
            self.autoLoader.stop()

    def __exit__(self, a, b, c):
        self.__del__()

    def __del__(self):
        self.autoLoader.stop()