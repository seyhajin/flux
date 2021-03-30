"""cleaning stuff"""

import os

from mods import flux, util, log, verb, target, build, project

from mods.build import BuildOpts
from mods.target import Target
from mods.project import Project

#------------------------------------------------------------------------------

def run(flux_dir, proj_dir, args):
    """clean intermediate project dirs"""
    if len(args) > 0:
        print(args)

        # clean opts
        opts = BuildOpts() #TODO: CleanOpts or global Opts?
        args = opts.parse_opts(proj_dir, args)

        # target
        #target = Target(flux_dir, opts)

        for arg in args:
            arg = util.fix_path(arg)
            path = os.path.join(proj_dir, arg)

            proj = Project(flux_dir, path, opts)

            # change to project dir
            #os.chdir(os.path.abspath(path))

            # clean output dir
            if opts.verbose >= 1:
                log.info("cleaning `%s`: `%s`" % (proj.profile, proj.out_dir))
            proj.clean()
    else:
        # show usage
        usage()

def help():
    return 'clean intermediate project dirs'

def usage():
    log.text('(?) '+help()+'\n')
    log.optional('usage', 'clean [options] [projects]')

#------------------------------------------------------------------------------