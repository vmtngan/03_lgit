#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import sys
from hashlib import sha1


def parse_arguments():
    """
    Parse command line strings into Python objects.

    @return: (namespace) An object to take the attributes.
    """
    parser = ArgumentParser(prog='lgit',
        description='A lightweight version of git')
    parser.add_argument('command',
        help='specify which command to execute among ' +
        '[init|add|rm|config|commit|status|log|ls-files]')
    parser.add_argument('files', nargs="*",
        help='name of files to add content to the index')
    return parser.parse_args()


def contain_lgit_dir():
    """
    Check if directory contain .lgit directory.

    @return: (bool) True - contain.
                    False - no contain.
    """
    cur = os.getcwd()
    while cur != '/':
        if '.lgit' in os.listdir(cur):
            os.chdir(cur)
            return True
        cur = os.path.dirname(cur)
    return False


def have_command_error(command):
    """
    Check if a lgit command is typed in a directory
    which doesn't have (nor its parent directories)
    a .lgit directory.

    @return: (bool) True - init error.
                    False - no error.
    """
    if command != 'init' and not contain_lgit_dir():
        print('fatal: not a git repository ' +
            '(or any of the parent directories)')
        return True
    return False


def write_config():
    """Write LOGNAME to the config file."""
    config_file = os.open('.lgit/config', os.O_WRONLY)
    os.write(config_file, (os.environ['LOGNAME']).encode())
    os.close(config_file)


def init_lgit_dir():
    """Initialize .lgit directory."""
    dirs = ['.lgit',
            '.lgit/objects',
            '.lgit/commits',
            '.lgit/snapshots']
    files = ['.lgit/index',
             '.lgit/config']
    for dir in dirs:
        os.mkdir(dir)
    for file in files:
        os.mknod(file)
    write_config()


def handle_missing_lgit_dir():
    """Add missing parts in .lgit directory."""
    lgit_list = os.listdir('.lgit')
    if 'objects' not in lgit_list:
        os.mkdir('.lgit/objects')
    if 'commits' not in lgit_list:
        os.mkdir('.lgit/commits')
    if 'snapshots' not in lgit_list:
        os.mkdir('.lgit/snapshots')
    if 'index' not in lgit_list:
        os.mknod('.lgit/index')
    if 'config' not in lgit_list:
        os.mknod('.lgit/config')
        write_config()


def check_exist_lgit_dir():
    """
    Check if .lgit directory was exist or not.

    @return: (bool) True - exist.
                    False - no exist.
    """
    if os.path.exists('.lgit'):
        if os.path.isfile('.lgit'):
            print('fatal: Invalid gitfile format: .lgit')
        elif os.path.isdir('.lgit'):
            handle_missing_lgit_dir()
            print('Git repository already initialized.')
        return True
    return False


def execute_lgit_init():
    if not check_exist_lgit_dir():
        init_lgit_dir()


def check_empty_files(add_list):
    """
    Check if the list of files to add is empty or not.

    @return: (bool) True - no empty.
                    False - empty.
    """
    if not add_list:
        print("Nothing specified, nothing added." +
            "\nMaybe you wanted to say 'git add .'?")
        return False
    return True


def print_permission_error(file):
    print('error: open("%s"): Permission denied' % file)
    print('error: unable to index file %s' % file)
    print('fatal: adding files failed')


def get_sub_files_dir(dir):
    """
    Get all files in current directory
    and sub-directories.

    @param dir: (str) The directory name.

    @return: (list of str) List of files that
                           directory contains.
    """
    sub_files = []
    for root, dirs, files in os.walk(dir):
        for name in files:
            sub_files.append(os.path.join(root, name))
    return sub_files


def hash_sha1(content):
    """Hash content to SHA1."""
    return sha1(content).hexdigest()


def add(filename):
    """
    Make a copy of file content and save it in .lgit database.
    Update file information in the index file.

    @param filename: (str) The file name.
    @param exist: (bool) True - file exists.
                        False - file does not exist.
    """
    print(filename)


def lgit_add(filename):
    """
    Lgit add.

    @param filename: (str) The file name.
    @param exist: (bool) True - file exists.
                        False - file does not exist.
    """
    try:
        file = os.open(filename, os.O_RDONLY)
        content = os.read(file, os.stat(file).st_size)
    except PermissionError:
        print_permission_error(filename)
    add(filename)
    os.close(file)


def execute_lgit_add(add_list):
    for item in add_list:
        if os.path.exists(item):
            if os.path.isfile(item):
                lgit_add(item)
            elif os.path.isdir(item):
                sub_list = get_sub_files_dir(item)
                execute_lgit_add(sub_list)
        elif os.getcwd() not in item:
            print("fatal: %s '%s' is outside " +
                "repository" % (item, item))
        else:
            print("fatal: pathspec '" + item +
                "' did not match any files")


def main():
    """Run the main program."""
    args = parse_arguments()
    if not have_command_error(args.command):
        if args.command == 'init':
            execute_lgit_init()
        elif args.command == 'add':
            if check_empty_files(args.files):
                execute_lgit_add(args.files)
        elif args.command == 'rm':
            execute_lgit_rm()
        elif args.command == 'config':
            execute_lgit_config()
        elif args.command == 'commit':
            execute_lgit_commit()
        elif args.command == 'status':
            execute_lgit_status()
        elif args.command == 'ls-files':
            execute_lgit_lsfiles()
        elif args.command == 'log':
            execute_lgit_log()


if __name__ == '__main__':
    main()
