#!/usr/bin/env python
'''flux main entry'''

import os
import sys

from mods import flux, log, util

# consts
DIR = 'flux' # flux dir name
EXE = 'flux' # flux exe name

# flux dir
flux_dir = util.split_dir(os.path.abspath(__file__))

# add flux dir to PYTHON system path
os.sys.path.insert(0, flux_dir)

# change current dir to 'workspace' dir
proj_dir = os.getcwd() # start_dir
curr_dir = proj_dir
while not util.is_root_dir(os.getcwd()) and \
      not os.path.isfile(os.path.join(os.getcwd(), DIR, EXE)):
    curr_dir = util.fix_path(util.split_dir(os.getcwd()))
    os.chdir(curr_dir)

# globals
work_dir = util.fix_path(curr_dir)
flux_exe = util.fix_path(os.path.join(work_dir, DIR, EXE))

# set env vars
os.environ['FLUX_WORKSPACE_DIR'] = work_dir
os.environ['FLUX_DIR'] = flux_dir
os.environ['FLUX_EXE'] = flux_exe

# check flux exe
if not os.path.isfile(flux_exe):
    log.fatal('unable to locate `%s` executable' % flux_exe)
#else:
#    log.info('`%s` executable found at `%s`' % (EXE, flux_exe))

# run flux
flux.run(flux_dir, proj_dir, sys.argv)
