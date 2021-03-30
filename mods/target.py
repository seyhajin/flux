
import os.path

from mods import log, util

#------------------------------------------------------------------------------ consts

# family targets
TARGET_DESKTOP = ['linux', 'macos', 'windows', 'windows-msvc', 'raspbian']
TARGET_MOBILE = ['android', 'ios', 'ios-sim']
TARGET_WEB = ['emscripten']
TARGET_TV = ['tvos']
TARGET_CONSOLE = []

TARGET = \
    TARGET_DESKTOP + \
    TARGET_MOBILE + \
    TARGET_WEB + \
    TARGET_TV + \
    TARGET_CONSOLE

CONFIG = [
    'debug',
    'release',
]

ARCH = [
    'x86',
    'x64',
    'arm32',
    'arm64',
    'wasm',
]

TOOLCHAIN = [
    'gcc',
    'msvc',
]

#------------------------------------------------------------------------------

class Target:

    #------------------------------------------------------------------------------
    def __init__(self, flux_dir, build_opts):
        '''Load target setting values from yaml datas'''

        data = util.load_flux_yaml(os.path.join(util.get_targets_dir(flux_dir), build_opts.target + '.yml'), build_opts)

        self.data = data
        self.target = data['target']
        self.toolchain = data['toolchain'] if data.get('toolchain') else 'gcc'

        #TODO: Distinct objc (*.m), objcxx (*.mm), staticlink (*.a), sharedlink (*.so, *.dll, *.dylib), link (app), 'as' to 'asm'

        # commands
        self.cmds = data['commands'] if data.get('commands') else {}
        self.cmds['cc'] = data['commands']['cc']  if data['commands'].get('cc')  else 'gcc'
        self.cmds['cxx']= data['commands']['cxx'] if data['commands'].get('cxx') else 'g++'
        self.cmds['as'] = data['commands']['as']  if data['commands'].get('as')  else 'as'
        self.cmds['ar'] = data['commands']['ar']  if data['commands'].get('ar')  else 'ar'
        self.cmds['ld'] = data['commands']['ld']  if data['commands'].get('ld')  else 'g++'

        # options
        self.opts = data['options'] if data.get('options') else {}
        self.opts['cc'] = data['options']['cc']  if data['options'].get('cc')  else ''
        self.opts['cxx']= data['options']['cxx'] if data['options'].get('cxx') else ''
        self.opts['as'] = data['options']['as']  if data['options'].get('as')  else ''
        self.opts['ar'] = data['options']['ar']  if data['options'].get('ar')  else ''
        self.opts['ld'] = data['options']['ld']  if data['options'].get('ld')  else ''

        # rules
        self.rules = data['rules'] if data.get('rules') else {}
        self.rules['cc'] = data['rules']['cc']  if data['rules'].get('cc')  else ''
        self.rules['cxx']= data['rules']['cxx'] if data['rules'].get('cxx') else ''
        self.rules['as'] = data['rules']['as']  if data['rules'].get('as')  else ''
        self.rules['ar'] = data['rules']['ar']  if data['rules'].get('ar')  else ''
        self.rules['ld'] = data['rules']['ld']  if data['rules'].get('ld')  else ''

    #------------------------------------------------------------------------------
    def __repr__(self):
        return \
            '%s==== target: %s, %s\n' % (log.YELLOW, self.target, self.toolchain) + \
            '%scommands:%s %s\n' % (log.BLUE, log.DEFAULT, self.cmds) + \
            '%soptions :%s %s\n' % (log.BLUE, log.DEFAULT, self.opts) + \
            '%srules   :%s %s'   % (log.BLUE, log.DEFAULT, self.rules)

    #------------------------------------------------------------------------------
    def get_rule_vars(self, proj):
        return {
            'target.cmds.cc'      : self.cmds['cc'],
            'target.cmds.cxx'     : self.cmds['cxx'],
            'target.cmds.ar'      : self.cmds['ar'],
            'target.cmds.as'      : self.cmds['as'],
            'target.cmds.ld'      : self.cmds['ld'],

            'target.opts.cc'      : self.opts['cc'],
            'target.opts.cxx'     : self.opts['cxx'],
            'target.opts.ar'      : self.opts['ar'],
            'target.opts.as'      : self.opts['as'],
            'target.opts.ld'      : self.opts['ld'],

            'project.opts.cc'     : ' '.join(proj.cc_opts),
            'project.opts.cxx'    : ' '.join(proj.cxx_opts),
            'project.opts.ar'     : ' '.join(proj.ar_opts),
            'project.opts.as'     : ' '.join(proj.as_opts),
            'project.opts.ld'     : ' '.join(proj.ld_opts),

            'project.out.file'    : proj.out_file,
            'project.libs'        : proj.lib_files,
            'project.objs'        : proj.obj_files,
            'project.source'      : '',
            'project.source.dep'  : '',
            'project.source.obj'  : '',
        }