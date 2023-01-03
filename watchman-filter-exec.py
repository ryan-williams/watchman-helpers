#!/usr/bin/env python
import click
import shlex
import sys
from subprocess import check_output, check_call


ARG_PLACEHOLDER = '{}'


@click.command('filter-files.py', help='Filter changed files output by `watchman`; by default, only output Git-tracked files.\n\n\twatchman-wait -m0 <dir> | filter-files.py [-G/--no-git-filter] [-p/--prefix <prefix>] [-v/--verbose...]')
@click.option('-G', '--no-git-filter', is_flag=True, help='Bypass filtering to Git-tracking files')
@click.option('-p', '--prefix', help='Filter to relative paths beginning with this prefix (and strip the prefix)')
@click.option('-v', '--verbose', count=True, help='1x: log to stderr when files pass filters and commands are run, and when the Git file listing is refreshed; 2x: also log files that are skipped')
@click.argument('args', nargs=-1)
def main(no_git_filter, prefix, verbose, args):
    args = list(args)
    if not args:
        args = ['echo']
    if all(ARG_PLACEHOLDER not in arg for arg in args):
        args += [ARG_PLACEHOLDER]

    do_git_filter = not no_git_filter
    if do_git_filter:
        git_files = list(filter(None, check_output(['git', 'ls-files']).decode().split('\n')))
    else:
        git_files = None

    def vlog(msg, level=1):
        if verbose >= level:
            sys.stderr.write(msg + '\n')

    for line in sys.stdin:
        file = line.rstrip('\n')
        if (no_git_filter or file in git_files) and (not prefix or file.startswith(prefix)):
            if prefix:
                file = file[len(prefix):]
            cmd = [
                arg.replace(ARG_PLACEHOLDER, file)
                for arg in args
            ]
            vlog(f'Running: {shlex.join(cmd)}')
            check_call(cmd)
        elif do_git_filter and file.startswith('.git/'):
            vlog(f'Refreshing Git file list ({file})')
            git_files = list(filter(None, check_output(['git', 'ls-files']).decode().split('\n')))
        else:
            vlog(f'Skipping: {file}', 2)


if __name__ == '__main__':
    main()
