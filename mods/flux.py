'''flux main module'''

import os, sys, shutil, subprocess

from packages.colorama import init
from packages import yaml
from mods import log, util, verb, target, project

from mods.build import BuildOpts
from mods.target import Target
from mods.project import Project

## TEMP
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
##/ TEMP


# set consts
VERSION = '0.0.1'

ninja_required_version = '1.10.2'

# init colorama
init()

#------------------------------------------------------------------------------

# workspace directory structure
#
# | $workspace_dir
#     `--| $flux_dir
#     `__| <others/others>
#           `--| $proj_dir

#------------------------------------------------------------------------------

def run(flux_dir, proj_dir, args):
    flux_dir = util.fix_path(flux_dir)
    proj_dir = util.fix_path(proj_dir)
    curr_dir = proj_dir

    # check space in project path
    if ' ' in proj_dir:
        log.warn('whitespace in project path detected, `flux` will not work correctly')

    # import verbs from flux dir
    verb.import_verbs(flux_dir)

    # parse args
    if len(args) <= 1:
        usage()
    else:
        name = args[1]
        args = args[2:]

        # run available verb
        if name in verb.verbs:
            verb.verbs[name].run(flux_dir, proj_dir, args)
        
        # for development stuff only
        elif name == 'dev':
            pass
        elif name == 'build':
            #log.text('===== test console output begin =====')
            #log.trace('trace message')
            #log.debug('debug message')
            #log.info('info message')
            #log.warn('warn message')
            #log.error('error message')
            #log.text('===== test console output end =====')

            # set build opts
            opts = BuildOpts()
            args = opts.parse_opts(proj_dir, args)

            # get target datas
            #TODO: add user custom targets 

            # set target opts
            target = Target(flux_dir, opts)
            if target.toolchain == 'msvc':
                # check msvc install
                if target.find_msvc():
                    # update env vars
                    os.environ['PATH'] = os.environ['FLUX_MSVC_PATH']+';'+os.environ['PATH']
                    os.environ['INCLUDE'] = os.environ['FLUX_MSVC_INCLUDE']
                    os.environ['LIB'] = os.environ['FLUX_MSVC_LIB']
                else:
                    log.fatal('MSVC installation not found!')
            elif target.target == 'emscripten':
                from mods.sdks import emsdk
                if emsdk.sdk_dir_exists(flux_dir):
                    os.environ['PATH'] += os.pathsep + emsdk.get_emscripten_dir(flux_dir)

            if opts.verbose >= 3:
                log.info('python %s.%s.%s' % (sys.version_info[:3]))
                log.info('os.environ:')
                for ev in sorted(filter(lambda x: x.startswith('FLUX_'), os.environ)):
                    log.info('- %s: %s' % (ev, log.YELLOW+os.environ[ev]+log.DEFAULT))

            # if not arg, set project in current dir
            if not len(args):
                args += [proj_dir]

            # for each projets
            for arg in args:
                print(log.YELLOW+("===== `%s`" % arg)+log.DEFAULT)
                arg = util.fix_path(arg)
                path = os.path.join(proj_dir, arg)

                #print(path)

                proj = Project(flux_dir, path, opts)

                # change to project dir
                os.chdir(os.path.abspath(path))

                # clean output dir
                if opts.clean:
                    if opts.verbose >= 1:
                        log.info("cleaning `%s`" % proj.out_dir)
                    proj.clean()

                # create project intermediate dirs
                proj.make_dirs()

                # make Info.plist file
                if proj.target == 'macos' and proj.apptype == 'window':
                    proj.make_info_plist()

                # parse project file
                proj.parse_inputs()

                #print(proj)
                
                # depends
                if proj.build in ['app']: # app only?
                    if len(proj.flux_libs):
                        sys_libs = []
                        for lib in proj.flux_libs:
                            # load dep project file
                            dep_dir = os.path.join(util.get_workspace_dir(flux_dir), lib)
                            dep = Project(flux_dir, dep_dir, opts, True)

                            # module or library dep only
                            if dep.build in ['mod', 'lib']:
                                # change dir to dep dir
                                cd = os.getcwd()
                                os.chdir(os.path.abspath(dep_dir))

                                # parse dep project file
                                dep.parse_inputs()

                                # files stamp
                                out_file_stamp = None
                                gen_file_stamp = None

                                # check if module archive exists
                                if not os.path.exists(dep.out_file):
                                    if not os.path.exists(dep.gen_file):
                                        #create dep intermediate dirs
                                        dep.make_dirs()

                                        # generate ninja file for dep
                                        if opts.verbose >= 1:
                                            log.info('generate `%s`' % dep.gen_file)
                                        with open(dep.gen_file, 'w') as out:
                                            dep.gen_ninja(out, opts, target)
                                else:
                                    #TODO: regenerate ninja if 'dep.flux_file' is most recent than 'dep.out_file'
                                    pass

                                # add 'dep.gen_file' to project
                                proj.ninja_files.append(dep.gen_file)

                                # build dep module
                                if os.path.exists(dep.gen_file):
                                    if opts.verbose >= 1:
                                        log.info('building `%s` %s' % (dep.base_dir, log.BLUE+'(dependency)'+log.DEFAULT))
                                    dep.build_ninja(verbose=opts.verbose>=3)

                                # add dep include dirs (abspath)
                                for inc in dep.include_dirs:
                                    proj.cc_opts.append('-I"%s"' % inc)
                                    proj.cxx_opts.append('-I"%s"' % inc)

                                # add dep module archive
                                proj.lib_files.append('"%s"' % dep.out_file)

                                # append system libs
                                for lib in dep.lib_files:
                                    if lib not in sys_libs:
                                        sys_libs.append(lib)

                                # return to main project
                                os.chdir(cd)

                        # add dep system libs at end
                        for lib in sys_libs:
                            if lib not in proj.lib_files:
                                proj.lib_files.append(lib)
                        
                # set rules vars
                #rule_vars = target.get_rule_vars(proj)

                # generate ninja in proj.out_dir
                if opts.verbose >= 1:
                    log.info('generate `%s`' % proj.gen_file)
                with open(proj.gen_file, 'w') as out:#StringIO()
                    proj.gen_ninja(out, opts, target)

                # build project from ninja
                if os.path.exists(proj.gen_file):
                    if opts.verbose >= 1:
                        log.info('building `%s`' % proj.base_dir)
                    proj.build_ninja(verbose=opts.verbose>=3)
                    # copy assets files
                    proj.copy_assets(proj.asset_dir)
                    proj.copy_binaries(proj.out_dir)

            # return to start dir
            os.chdir(curr_dir)
        else:
            log.error('unknown verb `%s`' % name)

#------------------------------------------------------------------------------
def usage():
    log.info('flux %s' % VERSION)
    log.optional('\nusage', 'flux [verb] [opts] [projects]')
    log.text('\nverbs:')
    for verb_name in sorted(verb.verbs):
        log.item('  '+verb_name, verb.verbs[verb_name].help())
    log.info('run `flux help` for more informations ') #TODO: Add all usage