import time
import importlib
import os
import re
from threading import Thread

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

    def get_content(self, path):
        result = ''
        fileName = path.replace('.', os.sep) + '.py'
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