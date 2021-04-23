"""backend code for 'emsdk' sdk"""

import os, stat, sys, subprocess, shutil
from mods import log, util
from mods.tools import git

EMSDK_URL = "https://github.com/emscripten-core/emsdk.git"
EMSDK_DEFAULT_VERSION = 'latest'

#------------------------------------------------------------------------------

def get_sdk_dir(flux_dir):
    return os.path.join(util.get_sdks_dir(flux_dir), 'emsdk')

def get_sdk_exe(flux_dir):
    sdk_exe = 'emsdk.bat' if util.get_host_platform() == 'windows' else 'emsdk'
    return os.path.join(get_sdk_dir(flux_dir), sdk_exe)

def get_sdk_config_file(flux_dir):
    '''returns the path to the local '.emscripten' file'''
    return os.path.join(get_sdk_dir(flux_dir), '.emscripten')

def sdk_dir_exists(flux_dir):
    return os.path.isdir(get_sdk_dir(flux_dir))

def sdk_exe_exists(flux_dir):
    return os.path.isfile(get_sdk_exe(flux_dir))

def get_emscripten_dir(flux_dir):
    '''returns the path where the "emcc", "em++" etc scripts are located'''
    config = parse_config(flux_dir)
    if 'EMSCRIPTEN_ROOT' in config:
        # older SDKs
        return config['EMSCRIPTEN_ROOT']
    else:
        # new SDKs
        return os.path.join(config['BINARYEN_ROOT'], 'emscripten')

#------------------------------------------------------------------------------

def run(flux_dir, cmd_line):
    if not sdk_exe_exists(flux_dir):
        log.error('emsdk script not found at "%s", please run "./flux emsdk install"' % get_sdk_exe(flux_dir))
    sdk_exe = get_sdk_exe(flux_dir)
    sdk_dir = get_sdk_dir(flux_dir)
    cmd = '%s %s' % (sdk_exe, cmd_line)
    subprocess.call(cmd, cwd=sdk_dir, shell=True)

#------------------------------------------------------------------------------ commands

def list(flux_dir):
    run(flux_dir, 'list')

def activate(flux_dir, sdk_version):
    if sdk_version is None:
        sdk_version = EMSDK_DEFAULT_VERSION
    log.colored(log.YELLOW, '=== activating "emscripten" SDK version "%s"' % sdk_version)
    run(flux_dir, 'activate --embedded %s' % sdk_version)

def install(flux_dir, sdk_version):
    res = False
    sdk_dir = get_sdk_dir(flux_dir)
    if sdk_dir_exists(flux_dir):
        res = update(flux_dir)
    else:
        res = clone(flux_dir)
    if not res:
        log.error('failed to install or update "emscripten" SDK')
    if sdk_version is None:
        sdk_version = EMSDK_DEFAULT_VERSION
    log.colored(log.YELLOW, '=== installing "emscripten" tools for "%s"' % sdk_version)
    run(flux_dir, 'install --shallow --disable-assertions %s' % sdk_version)
    activate(flux_dir, sdk_version)

def uninstall(flux_dir):
    sdk_dir = get_sdk_dir(flux_dir)
    log.colored(log.YELLOW, '=== uninstalling "emscripten" SDK at "%s"' % sdk_dir)
    clean(flux_dir)
    if sdk_dir_exists(flux_dir):
        log.info('deleting "%s"' % sdk_dir)
        shutil.rmtree(sdk_dir, onerror=util.remove_readonly)
    else:
        log.warn('emscripten SDK is not installed, nothing to do')
    
#------------------------------------------------------------------------------ configs

def parse_config(flux_dir):
    '''evaluate the ".emscripten" config file and returns key/value pairs of content'''
    config = {}
    config_path = get_sdk_config_file(flux_dir)    
    os.environ['EM_CONFIG'] = config_path
    try:
        with open(config_path, 'r') as f:
            config_text = f.read()
            exec(config_text, config)
    except Exception as e:
        log.error('error in evaluating ".emscripten" config file at "%s" with "%s"' % (config_path, str(e)))
    return config

def show_config(flux_dir):
    config = parse_config(flux_dir)
    for k, v in config.items():
        if k not in ['__builtins__', 'emsdk_path', 'os']:
            log.info('%s: %s' % (k, v))

#------------------------------------------------------------------------------ utils

def clone(flux_dir):
    sdk_dir = get_sdk_dir(flux_dir)
    if not sdk_dir_exists(flux_dir):
        log.colored(log.YELLOW, '===== cloning "emscripten" SDK to "%s"' % sdk_dir)
        util.make_sdks_dirs(flux_dir)
        sdks_dir = util.get_sdks_dir(flux_dir)
        return git.clone(EMSDK_URL, None, 1, 'emsdk', sdks_dir)

def update(flux_dir):
    sdk_dir = get_sdk_dir(flux_dir)
    if sdk_dir_exists(flux_dir):
        log.colored(log.YELLOW, '===== updating "emscripten" SDK at "%s"' % sdk_dir)
        return git.pull(sdk_dir)

def clean(flux_dir):
    '''this checks for any "old" SDKs and removes them'''
    old_sdk_dir = os.path.join(util.get_sdks_dir(flux_dir), util.get_host_platform())
    if os.path.isdir(old_sdk_dir):
        log.info('deleting "%s"' % old_sdk_dir)
        shutil.rmtree(old_sdk_dir, onerror=util.remove_readonly)
    else:
        log.info('nothing deleted')
