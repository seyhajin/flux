import os, sys, subprocess, glob, fnmatch

from shutil import rmtree, copyfile
from packages import yaml
from mods import util, log, build, ninja

#------------------------------------------------------------------------------

FILE        = 'flux.yml'    # default project file
FDIR        = 'flux-proj'   # intermediate dir
CACHE_DIR   = 'build'       # cache build dir
ASSET_DIR   = 'assets'      # assets dir
NINJA_FILE  = 'build.ninja'

# Ugly!!!!! from flux.py
VERSION = '0.0.1'
ninja_required_version = '1.10.2'

#------------------------------------------------------------------------------

#------------------------------
# project directory structure
#------------------------------
# project name: std
#
# base_dir  : std/
# build_dir : std/flux-proj/
# out_dir   : std/flux-proj/macos-release-x64/
# out_file  : std/flux-proj/macos-release-x64/*.xxx
# cache_dir : std/flux-proj/macos-release-x64/build/
# asset_dir : std/flux-proj/macos-release-x64/assets/
# gen_file  : std/flux-proj/macos-release-x64/build.ninja
#
#
# with 'outdir' in argument, ignore 'flux-proj' intermediate dir
#
# base_dir  : $outdir/std/
# build_dir : $outdir/std/
# out_dir   : $outdir/std/macos-release-x64/
# out_file  : $outdir/std/macos-release-x64/*.xxx
# cache_dir : $outdir/std/macos-release-x64/build/
# asset_dir : $outdir/std/macos-release-x64/assets/
# gen_file  : $outdir/std/macos-release-x64/build.ninja

#------------------------------------------------------------------------------

class Project:

    #------------------------------------------------------------------------------
    def __init__(self, flux_dir, proj_dir, build_opts):
        '''load project file and prepare intermediate dirs'''
        
        # project yaml datas
        self.data = None

        # init vars
        self.imported = {}

        # project inputs
        self.src_files = []
        self.lib_files = []
        self.obj_files = []
        self.bin_files = []
        self.java_files= []
        self.asset_files = []
        self.ninja_files = []

        # flux project
        self.flux_file = ''
        self.flux_srcs = []
        self.flux_libs = []

        # project build opts
        self.cc_opts = []
        self.cxx_opts= []
        self.ar_opts = []
        self.as_opts = []
        self.ld_opts = []

        self.include_dirs = []
        self.library_dirs = []

        # load project file datas
        proj_dir = util.fix_path(proj_dir)
        proj_file = ''
        if os.path.isdir(proj_dir):
            #log.track('is_dir: '+util.strip_dir(proj_dir), __file__)
            proj_files = [
                os.path.join(proj_dir, FILE),                               # flux.yml
                os.path.join(proj_dir, util.strip_dir(proj_dir) + '.yml'),  # <dirname>.yml
                os.path.join(proj_dir, util.strip_dir(proj_dir) + '.flux'), # <dirname>.flux
            ]
            for file in proj_files:
                #log.track('proj_file: '+file, __file__)
                if os.path.isfile(file):
                    proj_file = file
                    self.data = util.load_flux_yaml(proj_file, build_opts)
                    self.flux_file = proj_file
                    break

        elif os.path.isfile(proj_dir):
            #log.track('is_file: '+file, __file__)
            proj_file = proj_dir
            proj_dir = util.split_dir(proj_dir)
            self.data = util.load_flux_yaml(proj_file, build_opts)
            self.flux_file = proj_file
        
        if not self.data:
            log.fatal('unable to find project file in `%s`' % proj_dir)

        # get project name in project file else name will be the name of last folder
        self.name = self.data['name'] if self.data.get('name') else util.strip_dir(proj_dir)

        # update build opts
        build_opts.build = self.data['build'] if self.data.get('build') else 'app'
        build_opts.apptype = self.data['type'] if self.data.get('type') else 'window'
        build_opts.build = build.remap(build_opts.build)
        build_opts.target = build.remap(build_opts.target)

        # keep build options for project
        self.build = build_opts.build
        self.apptype = build_opts.apptype if build_opts.build == 'app' else '' # only for app
        self.profile = build_opts.profile
        self.target = build_opts.target
        self.toolchain = build_opts.toolchain

        # set project directory structure
        if build_opts.outdir:
            self.base_dir  = util.fix_path(build_opts.outdir)
            self.build_dir = util.fix_path(os.path.join(self.base_dir, self.name))
            self.out_dir   = util.fix_path(os.path.join(self.build_dir, build_opts.profile))
            self.cache_dir = util.fix_path(os.path.join(self.out_dir, CACHE_DIR))
            self.asset_dir = util.fix_path(os.path.join(self.out_dir, ASSET_DIR)
        )
        else:
            self.base_dir  = util.fix_path(proj_dir)
            self.build_dir = util.fix_path(os.path.join(self.base_dir, FDIR))
            self.out_dir   = util.fix_path(os.path.join(self.build_dir, build_opts.profile))
            self.cache_dir = util.fix_path(os.path.join(self.out_dir, CACHE_DIR))
            self.asset_dir = util.fix_path(os.path.join(self.out_dir, ASSET_DIR)
        )

        # get output extension
        self.out_ext = build.EXT[build_opts.target][build_opts.build]
        if self.target == 'macos' and self.build == 'app' and self.apptype != 'window':
            self.out_ext = '' # macos console app
        self.out_file = util.fix_path(os.path.join(self.out_dir, self.name + self.out_ext))

        # set gen file
        self.gen_file = util.fix_path(os.path.join(self.out_dir, NINJA_FILE))

        # get build options
        if 'options' in self.data:
            self.opts = self.data['options'] if self.data.get('options') else {}
            self.cc_opts.append(self.data['options']['cc']  if self.data['options'].get('cc')  else '')
            self.cxx_opts.append(self.data['options']['cxx'] if self.data['options'].get('cxx') else '')
            self.as_opts.append(self.data['options']['as']  if self.data['options'].get('as')  else '')
            self.ar_opts.append(self.data['options']['ar']  if self.data['options'].get('ar')  else '')
            self.ld_opts.append(self.data['options']['ld']  if self.data['options'].get('ld')  else '')

        # add build options for app
        if self.build in ['app', 'application']:
            # add workspace dir in header-dirs
            self.cc_opts.append('-I"%s"' % util.get_workspace_dir(flux_dir))
            self.cxx_opts.append('-I"%s"' % util.get_workspace_dir(flux_dir))
            # add project cache dir in header-dirs
            self.cc_opts.append('-I"%s"' % self.cache_dir)
            self.cxx_opts.append('-I"%s"' % self.cache_dir)
            # add project apptype
            if self.target == 'windows':
                if self.toolchain == 'msvc':
                    if self.apptype == 'window':
                        self.ld_opts.append('-subsystem:windows')
                    else:
                        self.ld_opts.append('-subsystem:console')
                else:
                    if self.apptype in ['window', 'gui']:
                        self.ld_opts.append('-mwindows')

    #------------------------------------------------------------------------------
    def __repr__(self):
        return \
            log.YELLOW + \
            '===== project `%s`: %s, %s, %s\n' % (self.name, self.build, self.apptype if self.apptype != '' else '_', self.profile) + \
            '- %sbase_dir :%s %s\n' % (log.BLUE, log.DEFAULT, self.base_dir) + \
            '- %sbuild_dir:%s %s\n' % (log.BLUE, log.DEFAULT, self.build_dir) + \
            '- %sout_dir  :%s %s\n' % (log.BLUE, log.DEFAULT, self.out_dir) + \
            '- %sout_file :%s %s\n' % (log.BLUE, log.DEFAULT, self.out_file) + \
            '- %sgen_file :%s %s\n' % (log.BLUE, log.DEFAULT, self.gen_file) + \
            '- %scache_dir:%s %s'   % (log.BLUE, log.DEFAULT, self.cache_dir) + \
            log.DEFAULT

    #------------------------------------------------------------------------------
    def clean(self):
        '''clean output project dir'''
        if os.path.exists(self.cache_dir):
            rmtree(self.out_dir)

    #------------------------------------------------------------------------------
    def make_dirs(self):
        '''create project intermediate dirs'''
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    #------------------------------------------------------------------------------
    def clean_ninja(self, cd=None, verbose=False):
        if cd is None:
            cd = os.getcwd()
        os.chdir(self.out_dir)
        if verbose:
            subprocess.call(['ninja', '-C', self.build_dir, '-f', self.gen_file, '-t', 'clean', '-v'], shell=True)
        else:
            subprocess.call(['ninja', '-C', self.build_dir, '-f', self.gen_file, '-t', 'clean'], shell=True)
        os.chdir(cd)

    #------------------------------------------------------------------------------
    def build_ninja(self, cd=None, verbose=False):
        if cd is None:
            cd = os.getcwd()
        os.chdir(self.out_dir)
        if verbose:
            subprocess.call(['ninja', '-C', self.build_dir, '-f', self.gen_file, '-v'], shell=True)
        else:
            subprocess.call(['ninja', '-C', self.build_dir, '-f', self.gen_file], shell=True)
        os.chdir(cd)

    #------------------------------------------------------------------------------
    def gen_ninja(self, file, build_opts, target):
        '''generate ninja build file from project'''
        rules_remap = {
            'target.cmds.cc'      : '$cc',
            'target.cmds.cxx'     : '$cxx',
            'target.cmds.ar'      : '$ar',
            'target.cmds.as'      : '$as',
            'target.cmds.ld'      : '$ld',

            'target.opts.cc'      : '$cc_opts_target',
            'target.opts.cxx'     : '$cxx_opts_target',
            'target.opts.ar'      : '$ar_opts_target',
            'target.opts.as'      : '$as_opts_target',
            'target.opts.ld'      : '$ld_opts_target',

            'project.opts.cc'     : '$cc_opts_project',
            'project.opts.cxx'    : '$cxx_opts_project',
            'project.opts.ar'     : '$ar_opts_project',
            'project.opts.as'     : '$as_opts_project',
            'project.opts.ld'     : '$ld_opts_project',

            'project.out.file'    : '$out',
            'project.libs'        : '$libs',
            'project.objs'        : '$objs',
            'project.source'      : '$in',
            'project.source.dep'  : '$dep_file',
            'project.source.obj'  : '$out', # $obj?
        }
        
        n = ninja.Writer(file, 150)

        n.comment('flux build system '+VERSION)
        n.comment('repo: https://github.com/seyhajin/flux')
        n.comment('this file is generated automatically, do not edit!')
        n.newline()
        n.variable('ninja_required_version', ninja_required_version)
        n.newline()
        n.comment('project settings')
        n.variable('proj_name', self.name)
        n.variable('proj_dir', self.base_dir)
        n.newline()
        n.comment('ninja settings')
        n.variable('builddir', self.cache_dir)
        n.newline()
        n.comment('target commands')
        n.variable('cc', target.cmds['cc'])
        n.variable('cxx', target.cmds['cxx'])
        n.variable('as', target.cmds['as'])
        n.variable('ar', target.cmds['ar'])
        n.variable('ld', target.cmds['ld'])
        n.newline()
        n.comment('target options')
        n.variable('cc_opts_target', target.opts['cc'])
        n.variable('cxx_opts_target', target.opts['cxx'])
        n.variable('as_opts_target', target.opts['as'])
        n.variable('ar_opts_target', target.opts['ar'])
        n.variable('ld_opts_target', target.opts['ld'])
        n.newline()
        n.comment('project options')
        n.variable('cc_opts_project', ' '.join(self.cc_opts))
        n.variable('cxx_opts_project', ' '.join(self.cxx_opts))
        n.variable('as_opts_project', ' '.join(self.as_opts))
        n.variable('ar_opts_project', ' '.join(self.ar_opts))
        n.variable('ld_opts_project', ' '.join(self.ld_opts))

        #TODO: add `subninja` for depends modules : used to include another .ninja file, introduces a new scope
        # `include` used to include another .ninja file in the current scope (use this only for global configurations)

        n.newline()
        n.comment('----------------------------')
        n.comment('RULES')
        n.comment('----------------------------')
        n.newline()

        #print(util.replace_env(target.rules['ar'], rules_remap))

        n.rule('cc_compile',
            util.replace_env(target.rules['cc'], rules_remap),
            deps=target.toolchain if target.toolchain in ['gcc', 'msvc'] else 'gcc',
            depfile=rules_remap['project.source.dep'],
            description='Compiling $in'
        )
        n.newline()

        n.rule('cxx_compile',
            util.replace_env(target.rules['cxx'], rules_remap),
            deps=target.toolchain if target.toolchain in ['gcc', 'msvc'] else 'gcc',
            depfile=rules_remap['project.source.dep'],
            description='Compiling $in'
        )
        n.newline()

        n.rule('as_compile',
            util.replace_env(target.rules['as'], rules_remap),
            #deps=target.toolchain if target.toolchain in ['gcc', 'msvc'] else 'gcc',
            description='Assembling $in'
        )
        n.newline()

        if self.build in ['mod', 'module']:
            n.rule('archive',
                util.replace_env(target.rules['ar'], rules_remap),
                description='Archiving $out'
            )
        elif self.build in ['app', 'application']:
            n.rule('link',
                util.replace_env(target.rules['ld'], rules_remap),
                description='Linking $out'
            )
        else:
            log.fatal('ninja: unrecognized project build type: `%s`' % self.build)

        n.newline()
        n.comment('----------------------------')
        n.comment('COMPILE')
        n.comment('----------------------------')
        n.newline()

        # for each project source file
        objs = []
        done = {}
        for src in self.src_files:
            ext = util.split_ext(src)
            obj = util.fix_path(os.path.join(self.cache_dir, os.path.relpath(src, self.base_dir)))
            dep = obj+'.d'
            obj += '.obj' if self.toolchain == 'msvc' else '.o'

            # relative paths
            src = util.fix_path(src.replace(self.base_dir, '$proj_dir'))
            obj = util.fix_path(obj.replace(self.cache_dir, '$builddir'))
            dep = util.fix_path(dep.replace(self.cache_dir, '$builddir'))

            # check if already done
            if obj in done:
                log.fatal('OOPS! collision! contact me!')
            done[obj] = True

            # build statement
            if ext in ['.c', '.m']:
                n.build(obj, 'cc_compile', src, variables={'dep_file': dep})
            elif ext in ['.cc', '.cxx', '.cpp', '.c++', '.mm']:
                n.build(obj, 'cxx_compile', src, variables={'dep_file': dep})
            elif ext in ['.asm', '.s']:
                n.build(obj, 'as_compile', src, variables={'file_name': src})
            
            # add obj to objects list
            objs.append(obj)

        objs += self.obj_files

        # objects alias
        n.newline()
        n.comment('objects alias')
        n.build('objects', 'phony ' + ' '.join(objs))

        if self.build in ['mod', 'module']:
            n.newline()
            n.comment('----------------------------')
            n.comment('ARCHIVE')
            n.comment('----------------------------')
            n.newline()
            n.build(
                self.out_file, 
                'archive || objects', 
                '',
                variables= {
                    'libs': self.lib_files,
                    'objs': ' '.join(objs),
                }
            )
        elif self.build in ['app', 'application']:
            n.newline()
            n.comment('----------------------------')
            n.comment('LINK')
            n.comment('----------------------------')
            n.newline()
            n.build(
                self.out_file, 
                'link || objects', 
                '',
                variables= {
                    'libs': self.lib_files,
                    'objs': ' '.join(objs),
                }
            )
        else:
            log.fatal('ninja: unrecognized project build type: `%s`' % self.build)

        # project alias
        n.newline()
        n.comment('project alias')
        n.build(self.name, 'phony ' + ninja.escape_path(self.out_file))

        n.newline()
        n.comment('----------------------------')
        n.comment('DEFAULT')
        n.comment('----------------------------')
        n.newline()
        n.build(
            'all',
            'phony %s %s' % (self.name, 'objects'),
        )
        n.newline()
        n.default('all')

        n.newline()
        n.close()

    #------------------------------------------------------------------------------
    def parse_inputs(self):
        '''parse inputs in project file'''
        # for each input entries
        for i in filter(lambda x: len(x), self.data['inputs']): #ignore empty
            # system
            if i.startswith('<') and i.endswith('>'):
                path = i[1:-1]
                self.parse_system_input(path)
            # local
            else:
                #If currentDir path=currentDir+path
                #ImportLocalFile( RealPath( path ) )
                path = i
                self.parse_local_input(path)

    #------------------------------------------------------------------------------
    def parse_system_input(self, path):
        '''parse system inputs'''
        name, ext = os.path.splitext(path)

        #if ext == '.flux':
        #    print('....parsing module deps....')
        #    # parsingModule.moduleDeps[name]=True

        # check if already imported
        if path in self.imported:
            return
        self.imported[path] = True

        # filter by extension
        if ext == '.a':
            if name.startswith('lib'):
                name = name[3:]
                if self.toolchain == 'msvc':
                    self.lib_files.append(name+'.lib')
                else:
                    self.lib_files.append('-l'+name)
            else:
                log.fatal('input error: `%s` - library file must be starts with `lib`and ends with `.a` extension.')
        elif ext == '.lib':
            if self.toolchain == 'msvc':
                self.lib_files.append(os.path.basename(path))
            else:
                self.lib_files.append('-l'+name)
        elif ext == '.dylib':
            if self.toolchain == 'gcc':
                self.lib_files.append('-l'+name)
        elif ext == '.framework':
            if self.toolchain == 'gcc':
                self.lib_files.append('-framework '+name)
        elif ext == '.weak_framework':
            if self.toolchain == 'gcc':
                self.lib_files.append('-weak_framework '+name)
        elif ext in ['.h', '.hh', '.hxx', '.hpp', '.h++']:
            pass # ignore
        elif ext == '.flux':
            self.flux_libs.append(name)
        else:
            log.fatal('unrecognized input file type: `%s`' % path)

    #------------------------------------------------------------------------------
    def parse_local_input(self, path):
        '''parse local inputs'''
        # check if already imported
        if path in self.imported:
            return
        self.imported[path] = True

        # assets
        i = path.find('@/')
        if i != -1:
            src = path[:i]
            if not os.path.exists(src):
                log.error('asset `%s` not found' % src)
                return
            self.asset_files.append(path)
            return

        # get name and extension
        name, ext = os.path.splitext(path)
        name = util.split_name(path)

        # filter by name
        if name == '*':
            path_dir = os.path.dirname(os.path.abspath(path))
            # check dir
            if not os.path.isdir(path_dir) and not path_dir.endswith('**'):
                log.fatal('input directory `%s` not found' % path_dir)
                return

            # filter by extension
            if ext == '.h':
                self.include_dirs.append(path_dir)
                self.cc_opts.append('-I"%s"' % path_dir)
                self.cxx_opts.append('-I"%s"' % path_dir)
            elif ext in ['.hh', '.hxx', '.hpp', '.h++']:
                self.include_dirs.append(path_dir)
                self.cxx_opts.append('-I"%s"' % path_dir)
            elif ext in ['.a', '.lib']:
                if self.toolchain == 'msvc':
                    self.library_dirs.append(path_dir)
                    self.ld_opts.append('-LIBPATH:"%s"' % path_dir)
                else:
                    self.library_dirs.append(path_dir)
                    self.ld_opts.append('-L"%s"' % path_dir)
            elif ext == '.dylib':
                if self.toolchain == 'gcc':
                    self.library_dirs.append(path_dir)
                    self.ld_opts.append('-L"%s"' % path_dir)
            elif ext == '.framework':
                if self.toolchain == 'gcc':
                    self.library_dirs.append(path_dir)
                    self.ld_opts.append('-F"%s"' % path_dir)
            elif ext in ['.c', '.cc', '.cxx', '.cpp', '.c++', '.m', '.mm', '.asm', '.s']:

                srcs = []
                if sys.version_info[:2] >= (3, 5):
                    srcs = glob.glob(os.path.join(path_dir, name+ext), recursive=True)
                else:
                    # recursive
                    if path_dir.endswith('**'):
                        path_dir = path_dir[:-3]
                        for dirpaths, _, files in sorted(os.walk(path_dir)):
                            for fn in fnmatch.filter(files, name+ext):
                                srcs.append(os.path.join(dirpaths, fn))
                    else:
                        srcs = glob.glob(os.path.join(path_dir, name+ext))
                if srcs:
                    for src in sorted(srcs):
                        if src in self.imported:
                            continue
                        self.imported[src] = True
                        self.src_files.append(os.path.abspath(src))
            else:
                log.fatal('unrecognized input file filter `%s%s`' % (name, ext))
            return

        # filter by extension
        if ext == '.framework':
            if self.toolchain == 'gcc':
                if not os.path.isdir(path):
                    log.fatal('input framework not found "%s"' % path)
                return
        elif ext == '.flux':
            log.fatal('input: flux module must be defined as a "system" input: `<%s>`' % path)
            return
        elif '$(TARGET_ARCH' not in path:
            if os.path.isdir(path):
                self.asset_files.append(path)
                return
            elif not os.path.isfile(path):
                log.fatal('input file not found "%s"' % path)

        if ext in ['.h', '.hh', '.hxx', '.hpp', '.h++']:
            pass # ignore
        elif ext in ['.c', '.cc', '.cxx', '.cpp', '.c++', '.m', '.mm', '.asm', '.s']:
            self.src_files.append(os.path.abspath(path))
        elif ext == '.java':
            if self.target == 'android':
                self.java_files.append(path)
        elif ext == '.o':
            self.obj_files.append(path)
        elif ext == '.lib':
            self.lib_files.append(path)
        elif ext == '.a':
            if self.toolchain == 'gcc':
                self.lib_files.append('"%s"' % path)
        elif ext in ['.so', '.dylib']:
            if self.toolchain == 'gcc':
                self.lib_files.append('"%s"' % path)
                self.bin_files.append(path)
        elif ext in ['.exe', '.dll']:
            if self.target == 'windows':
                self.bin_files.append(path)
        elif ext == '.framework':
            if self.toolchain == 'gcc':
                #TODO: Ugly!
                #parse_local_input(extract_dir(path)+'/*.framework')
                #parse_system_input(strip_dir(path))
                #self.bin_files.append(path)
                pass
        else:
            self.asset_files.append(path)

    #------------------------------------------------------------------------------
    def copy_assets(self, assets_dir):
        if not assets_dir.endswith('/'):
            assets_dir+='/'
        asset_files = {}
        for src in self.asset_files:
            dst = assets_dir
            if src.find('@/'):
                src, _, dst = src.partition('@/')
                if not dst.endswith('/'):
                    dst+='/'
            if os.path.isfile(src):
                dst+=util.strip_dir(src)
                self.enum_asset_files(src, dst, asset_files)
            elif os.path.isdir(src):
                self.enum_asset_files(src, dst, asset_files)
        if not len(asset_files):
            return

        # remove dest assets dir
        if os.path.exists(assets_dir):
            rmtree(assets_dir)

        # create dest assets dir
        os.makedirs(assets_dir)

        # copy asset files
        self.copy_asset_files(asset_files)

    #------------------------------------------------------------------------------
    def copy_binaries(self, bins_dir):
        if not bins_dir.endswith('/'):
            bins_dir+='/'
        for src in self.bin_files:
            bdir = bins_dir

            ext = util.split_ext(src)
            if ext != '':
                # dylibs for in Contents/MacOS dir...
                if ext == '.dylib':
                    bdir = os.path.abspath(bdir+'/')
                # frameworks go in app Contents/Frameworks dir
                elif ext == '.framework':
                    bdir = os.path.abspath(bdir+'../Frameworks/')
            dst = bdir + util.strip_dir(src)

            #FIXME: Hack for copying frameworks on macos!
            if self.target == 'macos':
                if util.split_ext(dst).lower() == '.framework':
                    os.makedirs(util.split_dir(dst))
                    log.trace('copy_binairies: make dst dir...`%s`' % util.split_dir(dst))
                    if not subprocess.call('rm -f -R '+dst):
                        log.failed('copy_binaires: `rm`', 'failed')
                    if not subprocess.call('cp -f -R '+src+' '+dst):
                        log.failed('copy_binaires: `cp`', 'failed')

            if not self.copy_all(src, dst):
                log.failed('copy_binaires: copy `%s` to `%s`' % (src, dst), 'failed')

    #------------------------------------------------------------------------------
    def copy_asset_files(self, files):
        for dst, src in files.items():
            # create dest dir if not exist
            if not os.path.exists(util.split_dir(dst)):
                os.makedirs(util.split_dir(dst))
            # copy file from src to dest
            copyfile(src, dst)
            # check if copy exist
            if os.path.exists(dst):
                continue
            log.fatal('error copying asset file `%s` to `%s`' % (src, dst))

    #------------------------------------------------------------------------------
    def enum_asset_files(self, src, dst, files):
        if os.path.isfile(src):
            if dst not in files:
                files[dst] = src
        elif os.path.isdir(src):
            for f in os.listdir(src):
                self.enum_asset_files(os.path.join(self.base_dir, src, f), os.path.join(self.out_dir, dst, f), files)

    #------------------------------------------------------------------------------
    def copy_all(self, src, dst):
        if os.path.isfile(src):
            if not os.makedirs(util.split_dir(dst)): 
                return False
            if not copyfile(src, dst): 
                return False
            log.trace('copy_all: make dirs...`%s`' % util.split_dir(dst))
            return True
        elif os.path.isdir(src):
            if not os.makedirs(dst): 
                return False
            log.trace('copy_all: make dirs...`%s`' % dst)
            for file in os.listdir(src):
                if not self.copy_all(os.path.join(src, file), os.path.join(dst, file)) : 
                    return False
                log.trace('copy_all: `%s` to `%s`' % (os.path.join(src, file), os.path.join(dst, file)))
            return True
        return False

    #------------------------------------------------------------------------------
    def make_info_plist(self):
        app_dir = self.out_file + '/'
        app_name= self.name

        out_file = app_dir+'Contents/MacOS/'+app_name
        assets_dir = app_dir+'Contents/Resources/'
        #bins_dir = util.split_dir(out_file)

        # make dirs
        if not os.path.exists(app_dir):
            os.makedirs(app_dir+'Contents/MacOS')
            os.makedirs(app_dir+'Contents/Resources')

        plist = \
            '<?xml version="1.0" encoding="UTF-8"?>\n' \
            '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n' \
            '<plist version="1.0">\n' \
            '<dict>\n' \
            '\t<key>CFBundleExecutable</key>\n' \
            '\t<string>'+app_name+'</string>\n' \
            '\t<key>CFBundleIconFile</key>\n' \
            '\t<string>'+app_name+'</string>\n' \
            '\t<key>CFBundlePackageType</key>\n' \
            '\t<string>APPL</string>\n' \
            '\t<key>NSHighResolutionCapable</key> <true/>\n' \
            '</dict>\n' \
            '</plist>\n'

        # create Info.plist
        file = open(app_dir+'Contents/Info.plist', 'w')
        file.write(plist)
        file.close()

        # change out_file, asset_dir
        self.out_file = out_file
        self.asset_dir = assets_dir
        #self.bins_dir = bins_dir


