
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
        self.buildopts = build_opts
        self.target = data['target']
        self.toolchain = data['toolchain'] if data.get('toolchain') else 'gcc'
        if self.toolchain == 'msvc':
            self.msvc_version = data['msvc-version'] if data.get('msvc-version') else [2019, 2017, 2015]
            self.msvc_prefix = data['msvc-prefix'] if data.get('msvc-prefix') else 'Note: including file:'

        # update build opts
        if build_opts.toolchain != self.toolchain:
            log.warn('toolchain build option `%s` is different to target toolchain `%s`' % (build_opts.toolchain, self.toolchain))
            build_opts.toolchain = self.toolchain

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

    #------------------------------------------------------------------------------
    def find_msvc(self):

        def find_max_ver_dir(ver_dir):
            max_ver = 0
            max_ver_dir = ''

            for f in os.listdir(ver_dir):
                ver_dir = os.path.join(ver_dir, f)
                if not os.path.isdir(ver_dir):
                    continue
                ver = int(f.replace('.', ''))
                if ver > max_ver:
                    max_ver = ver
                    max_ver_dir = ver_dir
            return max_ver_dir

        if self.toolchain == 'msvc':
            # MSVC
            msvcs = ''
            for ver in self.msvc_version:
                msvcs = os.path.join(os.environ['ProgramFiles(x86)'], 'Microsoft Visual Studio', str(ver).strip())
                if os.path.isdir(msvcs):
                    break
            if not os.path.isdir(msvcs):
                return False

            # Windows Kits
            wkits = os.path.join(os.environ['ProgramFiles(x86)'], 'Windows Kits\\10')
            if not os.path.isdir(wkits):
                return False

            # VC Tools
            tools_dir = ''
            max_ver = 0
            for f in os.listdir(msvcs):
                d = os.path.join(msvcs, f, 'VC\\Tools\\MSVC')
                if not os.path.isdir(d):
                    continue
                
                for ff in os.listdir(d):
                    ver_dir = os.path.join(d, ff)
                    if not os.path.isdir(ver_dir):
                        continue
                    ver = int(ff.replace('.', ''))
                    if ver > max_ver:
                        tools_dir = ver_dir
                        max_ver = ver

            # VC Includes
            incs_dir = find_max_ver_dir(os.path.join(wkits, 'Include'))
            if not incs_dir:
                return False

            # VC Libs
            libs_dir = find_max_ver_dir(os.path.join(wkits, 'Lib'))
            if not libs_dir:
                return False

            # show msvc dirs
            if self.buildopts.verbose >= 3:
                log.info('MSVC installation auto-detected: %s"%s"%s' % (log.YELLOW, msvcs, log.DEFAULT))
                log.info('- VC Tools   = %s"%s"%s' % (log.YELLOW, tools_dir, log.DEFAULT))
                log.info('- VC Include = %s"%s"%s' % (log.YELLOW, incs_dir, log.DEFAULT))
                log.info('- VC Lib     = %s"%s"%s' % (log.YELLOW, libs_dir, log.DEFAULT))

            # set msvc env vars
            if self.buildopts.arch == 'x86':
                os.environ['FLUX_MSVC_PATH'] = tools_dir+'\\bin\\Hostx86\\x86'
                os.environ['FLUX_MSVC_INCLUDE'] = tools_dir+'\\include;'+incs_dir+'\\ucrt;'+incs_dir+'\\shared;'+incs_dir+'\\um;'+incs_dir+'\\winrt'
                os.environ['FLUX_MSVC_LIB'] = tools_dir+'\\lib\\x86;'+libs_dir+'\\ucrt\\x86;'+libs_dir+'\\um\\x86'
            elif self.buildopts.arch == 'x64':
                os.environ['FLUX_MSVC_PATH'] = tools_dir+'\\bin\\Hostx64\\x64'
                os.environ['FLUX_MSVC_INCLUDE'] = tools_dir+'\\include;'+incs_dir+'\\ucrt;'+incs_dir+'\\shared;'+incs_dir+'\\um;'+incs_dir+'\\winrt'
                os.environ['FLUX_MSVC_LIB'] = tools_dir+'\\lib\\x64;'+libs_dir+'\\ucrt\\x64;'+libs_dir+'\\um\\x64'
            else:
                log.fatal('unrecognized architecture build option `%s`' % self.opts.arch)

            return True
        else:
            return False



            