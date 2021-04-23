"""emsdk installation and maintenance"""

from mods import flux, log
from mods.sdks import emsdk

#------------------------------------------------------------------------------

def run(flux_dir, proj_dir, args):
    if len(args) > 0:
        cmd = args[0]
        if cmd == 'install':
            sdk_version = None
            if len(args) > 1:
                sdk_version = args[1]
            emsdk.install(flux_dir, sdk_version)
        elif cmd == 'activate':
            sdk_version = None
            if len(args) > 1:
                sdk_version = args[1]
                emsdk.activate(flux_dir, sdk_version)
            else:
                log.error('emscripten SDK version expected (run "./flux emsdk list")')
        elif cmd == 'list':
            emsdk.list(flux_dir)
        elif cmd == 'uninstall':
            emsdk.uninstall(flux_dir)
        elif cmd == 'show-config':
            log.info('emscripten root directory: ' + emsdk.get_emscripten_dir(flux_dir))
            log.info('emscripten config file: ' + emsdk.get_sdk_config_file(flux_dir))
            emsdk.show_config(flux_dir)
        else:
            log.error('unknown subcommand "%s" (run "./flux help emsdk")' % cmd)
    else:
        log.error('expected a subcommand. run "./flux help emsdk" for help')

def help():
    return 'install and maintain the emscripten SDK'

def usage():
    log.text('(?) '+help()+'\n')
    log.optional('usage', 'emsdk <command>')
    log.colored(log.DEFAULT, '\ncommands: ')
    log.item('  list                    ', 'list emscripten SDKs')
    log.item('  install [sdk-version]   ', 'install specified emsdk version. (defaults: latest if ommit)')
    log.item('  activate <sdk-version>  ', 'activate installed emsdk version')
    log.item('  uninstall               ', 'uninstall emscripten SDK')
    log.item('  show-config              ', 'show emscripten configurations')


#------------------------------------------------------------------------------