'''various utility functions'''

import os.path
import sys
import platform
import multiprocessing
import re
from packages import yaml

host_platforms = {
    'Darwin':   'macos',
    'Linux':    'linux',
    'Windows':  'windows',
}

#------------------------------------------------------------------------------ system
def get_host_platform():
    pf = platform.system()
    if 'CYGWIN_NT' in pf:
        return host_platforms['Linux']
    return host_platforms[pf]

def get_num_cpucores():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 2

#------------------------------------------------------------------------------ workspace/project

def get_workspace_dir(flux_dir):
    # get workspace (parent) dir from `wake` dir
    return split_dir(flux_dir)

def get_targets_dir(flux_dir):
    return os.path.join(flux_dir, 'targets')

def get_verbs_dir(flux_dir):
    return os.path.join(flux_dir, 'verbs')

#------------------------------------------------------------------------------ filesystem

def fix_path(path):
    return path.replace('\\', '/')

def split_root_dir(path):
    '''Extracts the root directory from a file system path.'''
    path = fix_path(path)

    if path.startswith('//'): return '//'
    if path.startswith('/'): return '/'

    i = path.find('/')
    if path.startswith('$') and i != -1: return path[0:i+1]

    j = path.find(':')
    if j == -1 or (i != -1 and j>i): return ''

    if path[j:j+3] == '://': return path[0:j+3]
    if path[j:j+2] == ':/': return path[0:j+2]
    if path[j:j+2] == '::': return path[0:j+2]

    return ''

def is_root_dir(path):
    '''Checks if a path is a root directory.'''
    root = split_root_dir(path)
    return root != '' and len(root) == len(path)

def split_dir(path):
    '''Extracts the directory component from a filesystem path.'''
    return os.path.dirname(fix_path(path))

def split_name(path):
    '''Extracts the filename without extension component from a filesystem path.'''
    return os.path.splitext(strip_dir(path))[0]

def split_file(path):
    '''Extracts the extension component from a filesystem path.'''
    return os.path.splitext(fix_path(path))[0]

def split_ext(path):
    '''Extracts the extension component from a filesystem path.'''
    return os.path.splitext(fix_path(path))[1]

def strip_dir(path):
    '''Strips the directory component from a filesystem path.'''
    return os.path.basename(fix_path(path))

def strip_ext(path):
    '''Strips the extension component from a filesystem path.'''
    return os.path.split(fix_path(path))[0]

#------------------------------------------------------------------------------ misc

def replace_env(txt, dic):
    '''replace environment variables in text with dict'''
    pattern = re.compile(r'.*?\${([A-Za-z0-9._-]+)}.*?')
    match = pattern.findall(txt)
    if match:
        new_txt = txt
        for g in match:
            new_txt = new_txt.replace('${%s}' % str(g), str(dic.get(g, g)))
        return new_txt
    return txt

def enquote(txt, quote='"'):
    return quote+txt+quote

#------------------------------------------------------------------------------ yaml

def load_flux_yaml(file, opts):
    '''load flux yaml file'''

    file = fix_path(file)

    # pattern for global vars: look for ${word}
    pattern = re.compile(r'.*?\${([A-Za-z0-9._-]+)}.*?')
    loader = yaml.SafeLoader

    # the tag will be used to mark where to start searching for the pattern
    # e.g. somekey: !$env somestring${MYENVVAR}blah blah blah
    loader.add_implicit_resolver('!$env', pattern, None)

    #---------------------------------------
    # defines custom tag handlers
    #---------------------------------------

    def env(loader, node):
        '''Extracts the environment variable from the node's value'''
        value = loader.construct_scalar(node)
        match = pattern.findall(value) # to find all env variables in line
        if match:
            new_value = value
            for g in match:
                new_value = new_value.replace('${%s}' % g, os.environ.get(g, g))
            return new_value
        return value

    # add direction join function when parse the yaml file
    def join(loader, node):
        seq = loader.construct_sequence(node)
        return os.path.sep.join(seq)

    # add string concatenation function when parse the yaml file
    def concat(loader, node):
        seq = loader.construct_sequence(node)
        return ' '.join([str(i) for i in seq if str(i) != ''])

    #TODO: add conditional function when parse the yaml file
    #def iif(loader, node):
    #    value = loader.construct_scalar(node)
    #    return value if cond else ''
    
    # targets
    def if_linux(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.target == 'linux' else ''

    def if_macos(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.target == 'macos' else ''

    def if_windows(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.target == 'windows' else ''
    
    # configs
    def if_debug(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.config == 'debug' else ''

    def if_release(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.config == 'release' else ''

    # archs
    def if_x86(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.arch == 'x86' else ''

    def if_x64(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.arch == 'x64' else ''

    def if_arm32(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.arch == 'arm32' else ''

    def if_arm64(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.arch == 'arm64' else ''

    def if_wasm(loader, node):
        value = loader.construct_scalar(node)
        return value if opts.arch == 'wasm' else ''

    #---------------------------------------
    # register the tag handlers
    #---------------------------------------

    yaml.add_constructor('!$env', env)

    yaml.add_constructor('!join', join)
    yaml.add_constructor('!concat', concat)
    yaml.add_constructor('!flags', concat) # extra
    yaml.add_constructor('!opts', concat) # extra
    yaml.add_constructor('!args', concat) # extra

    #yaml.add_constructor('!?macos', iif(opts.target == 'macos'))

    yaml.add_constructor('!?linux', if_linux)
    yaml.add_constructor('!?macos', if_macos)
    yaml.add_constructor('!?windows', if_windows)

    #TODO: Add 'ios', 'android', 'darwin' for macos|ios|tvos, 'mobile', 'desktop', 'web', 'tv', 'console'

    yaml.add_constructor('!?debug', if_debug)
    yaml.add_constructor('!?release', if_release)

    yaml.add_constructor('!?x86', if_x86)
    yaml.add_constructor('!?x64', if_x64)
    yaml.add_constructor('!?arm32', if_arm32)
    yaml.add_constructor('!?arm64', if_arm64)
    yaml.add_constructor('!?wasm', if_wasm)

    #---------------------------------------
    # Load yaml file and return yaml object
    #---------------------------------------
    with open(file, 'r') as f:
        data = yaml.full_load(f)
        f.close()
    return data