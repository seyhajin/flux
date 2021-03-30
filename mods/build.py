
import os.path

from mods import log, util, target

#------------------------------------------------------------------------------ consts

BUILD_TYPE = ['application', 'app', 'module', 'mod', 'library', 'lib', 'staticlib', 'sharedlib']
APP_TYPE   = ['window', 'console']

# output file ext: [target][build]
EXT = {
    'windows': {
        'app': '.exe',
        'mod': '.a',
        'lib': '.dll',
    },
    'windows-msvc': {
        'app': '.exe',
        'mod': '.lib',
        'lib': '.dll',
    },
    'linux': {
        'app': '',
        'mod': '.a',
        'lib': '.so',
    },
    'macos': {
        'app': '.app',
        'mod': '.a',
        'lib': '.dylib',
    },
    'raspbian': {
        'app': '',
        'mod': '.a',
        'lib': '.so',
    },
    'emscripten': {
        'mod': '.bc',
    },
}

# aliases
aliases = {
    'application' : 'app',
    'module'      : 'mod',
    'libray'      : 'lib',
    #
    'staticlib'   : 'mod',
    'sharedlib'   : 'lib',
    #
    'win'         : 'windows',
    'win-msvc'    : 'windows-msvc',
    'osx'         : 'macos',
    'rpi'         : 'raspbian',
    'emsc'        : 'emscripten',
    #
    'gui'         : 'window',
    'windowed'    : 'window',
}

def remap(name):
    if name in aliases:
        return aliases[name]
    return name

#------------------------------------------------------------------------------

class BuildOpts:
    '''Build options'''

    #------------------------------------------------------------------------------
    def __init__(self, target='desktop', config='debug', arch='x64', tag='', toolchain='gcc'):
        # build options
        self.target = target
        self.config = config
        self.arch = arch
        self.tag = tag
        self.toolchain = toolchain

        # init options
        self.build = ''
        self.apptype = 'window'
        self.args = ''
        self.outdir = ''
        self.profile = '' # profile + tag
        self.clean = False
        self.time = False
        self.verbose = 0

    #------------------------------------------------------------------------------
    def parse_opts(self, proj_dir, args):
        '''parse build options'''
        self.args = args

        # parse arguments
        i = 0
        for arg in args:
            # options without params
            if arg in ['-v', '-verbose']:
                self.verbose = 1
            elif arg in ['-t', '-time']:
                self.time = True
            elif arg in ['-c', '-clean']:
                self.clean = True
            else:
                # options with params
                if arg.startswith('-'):
                    i = arg.find('=')
                    if i == -1:
                        log.fatal('expected value for option `%s`' % arg)

                    opt, _, val = arg.partition('=')
                    path = util.fix_path(val)
                    if path.startswith('"') and path.endswith('"'):
                        path = path[1:-1]

                    opt = opt.lower()
                    val = val.lower()

                    # outdir (output dir)
                    if opt in ['-o', '-outdir']:
                        # relative to current dir
                        self.outdir = os.path.abspath(os.path.join(proj_dir, path))
                    # apptype
                    elif opt == '-apptype':
                        if val in APP_TYPE:
                            self.apptype = val
                        else:
                            log.fatal('invalid value for `apptype` option: `{}` - must be {}'.format(val, APP_TYPE))
                    # target
                    elif opt == '-target':
                        if val in target.TARGET or val == 'desktop':
                            self.target = val
                        else:
                            log.fatal('invalid value for `target` option: `{}` - must be {} or `desktop`'.format(val, target.TARGET))
                    # config
                    elif opt == '-config':
                        if val in target.CONFIG:
                            self.config = val
                        elif val == 'all':
                            self.config = ','.join(target.CONFIG)
                        else:
                            log.fatal('invalid value for `config` option: `{}` - must be {} or `all`'.format(val, target.CONFIG))
                    # arch
                    elif opt == '-arch':
                        if val in target.ARCH:
                            self.arch = val
                        else:
                            log.fatal('invalid value for `arch` option: `{}` - must be {}'.format(val, target.ARCH))
                    # verbose
                    elif opt in ['-v', '-verbose']:
                        if val in ['0', '1', '2', '3', '-1']:
                            self.verbose = int(val)
                        else:
                            log.fatal('invalid value for `verbose` option: `{}` - must be {}'.format(val, "['0', '1', '2', '3' or '-1']"))
                    # profile
                    elif opt == '-profile':
                        #TODO: -profile=windows-msvc-release-x64; macos-release-x64 ; ios-sim-release-arm64 ; emscripten-release-wasm
                        log.todo('set profile config: <target>-<config>-<arch>[-<tag>]', __file__)
                        pass
                    # tag
                    elif opt == '-tag':
                        self.tag = val
                    else:
                        log.fatal('unrecognized option: `%s`' %arg)
                else:
                    #paths of project file
                    i = args.index(arg)
                    break
        
        # get project paths
        args = args[i:]

        # adjust build options
        if self.target == '' or self.target == 'desktop':
            self.target = util.get_host_platform()

        self.toolchain = 'gcc'

        if self.target in target.TARGET_DESKTOP:
            if self.apptype == '':
                self.apptype = APP_TYPE[0]
        elif self.target in target.TARGET and self.target not in target.TARGET_DESKTOP:
            log.todo("need to ajust other target options (%s)"%self.target, __file__)
        else:
            log.fatal('unrecognized target `%s` or not yet implemented' % self.target)

        if self.apptype in APP_TYPE:
            if self.target not in target.TARGET_DESKTOP:
                log.fatal('`apptype` `%s` is only valid for desktop targets' % self.apptype)
        else:
            log.fatal('unrecognized apptype `%s`' % self.apptype)

        # set built profile: <target>-<config>-<arch>[-<tag>]
        self.profile = '-'.join([self.target, self.config, self.arch]) + (('-' + self.tag) if self.tag else '')

        return args

    #------------------------------------------------------------------------------
    def __repr__(self):
        return \
            log.YELLOW + \
            '===== buildopts with args: %s\n' % (self.args) + \
            '%starget:%s %s, ' % (log.BLUE, log.DEFAULT, self.target) + \
            '%sconfig:%s %s, ' % (log.BLUE, log.DEFAULT, self.config) + \
            '%sarch:%s %s, ' % (log.BLUE, log.DEFAULT, self.arch) + \
            '%stag:%s %s, ' % (log.BLUE, log.DEFAULT, self.tag) + \
            '%stoolchain:%s %s, ' % (log.BLUE, log.DEFAULT, self.toolchain) + \
            '%sclean:%s %s, ' % (log.BLUE, log.DEFAULT, str(self.clean)) + \
            '%stime:%s %s, ' % (log.BLUE, log.DEFAULT, str(self.time)) + \
            '%sverbose:%s %s, ' % (log.BLUE, log.DEFAULT, str(self.verbose)) + \
            '%sapptype:%s %s'   % (log.BLUE, log.DEFAULT, self.apptype) + \
            log.DEFAULT