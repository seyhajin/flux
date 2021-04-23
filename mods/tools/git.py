"""wrapper for some git commands"""

import re, subprocess
from mods import log

# flux tool desc
name = 'git'
platforms = ['linux', 'macos', 'windows', 'raspbian']
optional = False
not_found = '"git" not found in path, can\'t happen(?)'

# flux tool vars
clone_depth = 10

#------------------------------------------------------------------------------

def exists(flux_dir=None, verbose=True):
    '''test if "git" is in the path'''
    try:
        subprocess.check_output(['git', '--version'])
        return True
    except(OSError, subprocess.CalledProcessError):
        if verbose:
            log.error('"git" not found in path, please run and fix `flux diag tools`')
        return False

#------------------------------------------------------------------------------

def clone(url, branch, depth, name, cwd):
    '''git clone a remote git repo'''
    exists()
    cmd = 'git clone --recursive'
    if branch:
        cmd += ' --branch %s --single-branch' % branch
    if depth:
        cmd += ' --depth %s' % depth
    cmd += ' %s %s' % (url, name)
    res = subprocess.call(cmd, cwd=cwd, shell=True)
    return res == 0

def add(proj_dir, update=False):
    '''run a "git add ." in the provided git repo'''
    exists()
    cmd = 'git add ' + '-u' if update else '.'
    try:
        subprocess.check_call(cmd, cwd=proj_dir, shell=True)
    except subprocess.CalledProcessError as e:
        log.error('"%s" failed with "%s"' % (cmd, e.returncode))

def commit(proj_dir, msg, allow_empty=False):
    '''runs a "git commit -m msg" in the provided git repo'''
    exists()
    cmd = 'git commit '+ ('--allow-empty ' if allow_empty else '') + ('-m "%s"' % msg)
    try:
        subprocess.check_call(cmd, cwd=proj_dir, shell=True)
    except subprocess.CalledProcessError as e:
        log.error('"git commit" failed with "%s"' % (e.returncode))

def push(proj_dir):
    '''runs a "git push" in the provided git repo'''
    exists()
    cmd = 'git push'
    try:
        subprocess.check_call(cmd, cwd=proj_dir, shell=True)
    except subprocess.CalledProcessError as e:
        log.error('"%s" failed with "%s"' % (cmd, e.returncode))

def status(proj_dir):
    '''checks if a git repo has uncommitted or unpushed changes'''
    exists()
    output = subprocess.check_output('git status --porcelain', cmd=proj_dir, shell=True).decode('utf-8')
    if output:
        return True
    # get current branch name and tracked remote if exists, this has either the form:
    #       ## master...origin/master [optional stuff]
    # ...if there's a remote tracking branch setup, or just
    #       ## my_branch
    # ...if this is a local branch
    cur_status = subprocess.check_output('git status -sb', cwd=proj_dir, shell=True).decode("utf-8")[3:].rstrip().split(' ')[0]
    if '...' in cur_status:
        str_index = cur_status.find('...')
        cur_branch = cur_status[:str_index]
        cur_remote = cur_status[str_index+3:]
    else:
        cur_branch = cur_status
        cur_remote = ''
    output = subprocess.check_output('git log {}..{} --oneline'.format(cur_remote, cur_branch),
            cwd=proj_dir, shell=True).decode("utf-8")
    if output:
        return True

def update(proj_dir):
    '''runs a "git pull && git submodule update --recursive" on the
    provided git repo, but only if the repo has no local changes'''
    exists()
    if not status(proj_dir): #has no local changes
        subprocess.call('git pull', cwd=proj_dir, shell=True)
        update_submodules(proj_dir)
        return True
    else:
        log.warn('skipping "%s", uncommitted or unpushed changes!' % proj_dir)
        return False

def pull(proj_dir): # update force and ignore local changes
    '''same as git.update() but does not check for local changes'''
    exists()
    res = subprocess.call('git pull -f', cwd=proj_dir, shell=True)
    if 0 == res:
        update_submodules(proj_dir)
    return 0 == res

def update_submodules(proj_dir):
    '''runs a 'git submodule sync --recursive' followed by a "git submodule update --recursive" on the provided git repo, unconditionally (it will *not* check for local changes)'''
    exists()
    try:
        subprocess.call('git submodule sync --recursive', cwd=proj_dir, shell=True)
        subprocess.call('git submodule update --recursive', cwd=proj_dir, shell=True)
    except subprocess.CalledProcessError:
        log.error('failed to call "git submodule sync/update"!')

def checkout(proj_dir, revision):
    '''checkout a specific revision hash of a repository'''
    exists()
    try:
        output = subprocess.check_output('git checkout %s' % revision, cwd=proj_dir, shell=True).decode('utf-8')
        update_submodules(proj_dir)
        return output.split(':')[0] != 'error'
    except subprocess.CalledProcessError:
        log.error('failed to call "git checkout %s"' % revision)
        return None

def branches(proj_dir):
    '''get a dictionary with all local branch names of a git repo as keys, and their remote branch names as value'''
    exists()
    branches = {}
    try:
        output = subprocess.check_output('git branch -vv', cwd=proj_dir, shell=True).decode('utf-8')
        lines = output.splitlines()
        for line in lines:
            tokens = line[2:].split()
            local_branch = tokens[0]
            if re.compile("^\[.*(:|\])$").match(tokens[2]):
                remote_branch = tokens[2][1:-1]
                branches[local_branch] = remote_branch
    except subprocess.CalledProcessError:
        log.error('failed to call "git branch -vv"')
    return branches