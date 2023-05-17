import importlib
import os

def enumerate_plugins(category = 'probes'):

    if category not in ('probes', 'detectors'):
        raise ValueError('Not a recognised plugin type:', category)
    
    pkg = importlib.import_module(f"{category}.base")

    base_plugin_classnames = set([n for n in dir(pkg) if not n.startswith('__')])
    plugin_class_names = {}

    for module_filename in os.listdir(category):
        if not module_filename.endswith('.py'):
            continue
        if module_filename.startswith('__') or module_filename == 'base.py':
            continue
        module_name = module_filename.replace('.py', '')
        #print(category, 'module:', module_name)
        mod = importlib.import_module(f"{category}.{module_name}")
        module_plugin_names = set([p for p in dir(mod) if not p.startswith('__')])
        module_plugin_names = module_plugin_names.difference(base_plugin_classnames)
        #print(' >> ', ', '.join(module_plugin_names))
        for module_probe_name in module_plugin_names:
            plugin_class_names[module_probe_name] = f"{category}.{module_name}.{module_probe_name}"

    return plugin_class_names

def load_plugin(path, break_on_fail=True): # input: sth like "probe.blank.BlankPrompt"; return class instance
    try:
        category, module_name, plugin_class_name = path.split('.')
    except ValueError:
        if break_on_fail:
            raise ValueError(f'Expected plugin name in format category.module_name.class_name, got "{path}"')
        else:
            return False
    try:
        mod = importlib.import_module(f"{category}.{module_name}")
    except:
        if break_on_fail:
            raise ValueError("Didn't successfully import " + module_name)
        else:
            return False
    
    try:
        plugin_instance = getattr(mod, plugin_class_name)()
    except AttributeError:
        if break_on_fail:
            raise ValueError(f"Plugin {plugin_class_name} not found in {category}.{module}")
        else:
            return False
    except Exception as e:
        print("error in: module", mod, "class", plugin_class_name)
        raise e
        
    return plugin_instance