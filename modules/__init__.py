import time
import importlib
import os
import re
from threading import Thread, Lock

class ModuleAutoLoader(Thread):
    def __init__(self, path, onModuleLoaded = None, onModuleAdded = None, onModuleDeleted = None, onModuleError = None):
        Thread.__init__(self)
        self.path = path
        self.onModuleLoaded = onModuleLoaded or (lambda path, module:path)
        self.onModuleAdded = onModuleAdded or (lambda path, module:path)
        self.onModuleDeleted = onModuleDeleted or (lambda path, module:path)
        self.onModuleError = onModuleError or (lambda path:path) 
        self.running = False
        self.executionEnded = False
        self.modules = {}
        self.fails = {}
        pass

    def get_content(self, path):
        result = ''
        fileName = '{0}.py'.format(path.replace('.', os.sep))
        with open(fileName) as f:
            result = f.read()
        return result

    def get_current_modules(self):
        files = [i[:-3] for i in os.listdir(self.path) if i.endswith('.py') and not i == '__init__.py']
        files = [i for i in files if len(re.findall(r'^[\w]+$', i)) > 0]
        return ['.'.join([self.path, i]) for i in files]

    def load_module(self, path):
        try:
            if path in self.fails.keys():
                return    
            isNewModule = True
            if path in self.modules.keys():
                isNewModule = False
                if path in importlib.sys.modules.keys():
                    del importlib.sys.modules[path]

            self.modules[path] = {"content":self.get_content(path)}
            self.modules[path]["module"] = importlib.import_module(path)

            if isNewModule:
                self.onModuleAdded(path, self.modules[path]["module"])
            self.onModuleLoaded(path, self.modules[path]["module"])
        except Exception as e:
            self.fails[path] = e
            self.onModuleError(path)

    def remove_module(self, path):
        if path in self.modules.keys():
            removedModule = self.modules[path]["module"]
            del self.modules[path]
            importlib.invalidate_caches()
            self.onModuleDeleted(path, removedModule)

    def run(self):
        if(self.running): return
        self.running = True
        self.executionEnded = False
        while self.running:
            time.sleep(1)
            oldModules = self.modules.keys()
            currentModules = self.get_current_modules()
            
            addedModules = [i for i in currentModules if i not in oldModules]
            removedModules = [i for i in oldModules if i not in currentModules]
            notVariantModules = [i for i in (set(oldModules) & set(currentModules))]

            for i in removedModules:
                self.remove_module(i)

            for i in addedModules:
                self.load_module(i)

            updatedModules = [i for i in notVariantModules if self.modules[i]["content"] != self.get_content(i)]
            for i in updatedModules:
                if i in self.fails.keys():
                    del self.fails[i]
                self.load_module(i)

        self.executionEnded = True

    def __del__(self):
        self.stop()
    
    def stop(self):
        self.running = False
        while not self.executionEnded:
            time.sleep(1)

class ModulesRunner:
    def __init__(self, path, methodsToFind, onPrint = None):
        self.onPrint = onPrint or (lambda x: print('Fromhere: {0}'.format(x)))
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
        self.onPrint('Module added : {0}'.format(path))
        pass

    def module_updated(self, path, module):
        self.mutex.acquire()
        self.onPrint('Module updated : {0}'.format(path))
        module.print = self.onPrint
        methods = [(getattr(module, i), i) for i in dir(module) if i in self.methodsToFind]
        methods = [i for i in methods if callable(i[0])]
        if(len(methods) > 0):
            self.onPrint(' :: Method: {0}.{1}'.format(path, methods[0][1]))
            self.methods[path] = methods[0][0]
        else:
            self.onPrint(' :: Not suitable method found in {0} : requested {1}'.format(path, self.methodsToFind))
        self.mutex.release()

    def module_removed(self, path, module):
        if path in self.methods.keys():
            self.onPrint('Module deleted : {0}'.format(path))
            del self.methods[path]
        pass
    
    def module_error(self, path):
        self.onPrint('Error on Module : {0}'.format(path))
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