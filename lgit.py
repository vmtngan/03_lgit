#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import sys
from hashlib import sha1
from datetime import datetime


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
    parser.add_argument('files', nargs='*',
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
    config_file = open('.lgit/config', 'w+')
    config_file.write(os.environ['LOGNAME'])
    config_file.close()


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


def check_empty_files(list, cmd):
    """
    Check if the list of files to add is empty or not.

    @param list:(list of str) The file list.
    @param cmd: (str) The command.

    @return: (bool) True - no empty.
                    False - empty.
    """
    if not list:
        print("Nothing specified, nothing added." +
            "\nMaybe you wanted to say 'git " + cmd + " .'?")
        return False
    return True


def print_permission_error(file):
    print('error: open("' + file + '"): Permission denied')
    print('error: unable to index file ' + file)
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


def create_file(cryp, content):
    """
    Create the file in objects directory.

    @param cryp: (str) SHA1 cryptography of the content.
    @param content: (str) The file content.
    """
    if not os.path.exists('.lgit/objects/' + cryp[:2]):
        os.mkdir('.lgit/objects/' + cryp[:2])
    file = os.open('.lgit/objects/' + cryp[:2] + '/' + cryp[2:],
        os.O_RDWR | os.O_CREAT)
    os.write(file, content)
    os.close(file)


def get_timestamp(filename):
    """
    Get timestamp of the file.

    @param filename: (str) The file name.
    """
    m_time = os.path.getmtime(filename)
    timestamp = datetime.fromtimestamp(m_time)
    return timestamp.strftime('%Y%m%d%H%M%S')


def get_start_pos(filename):
    """
    Get the starting position to write the file.

    @param filename: (str) The file name.

    @return: (int) The starting position.
    """
    start = 0
    with open('.lgit/index', 'r') as file:
        for line in file:
            if filename in line.split():
                break
            start += len(line)
    return start


def update_index_add(cryp, filename):
    """
    Update file information in the index file (add).

    @param cryp: (str) SHA1 cryptography of the content.
    @param filename: (str) The file name.
    """
    index_file = os.open('.lgit/index', os.O_RDWR)
    os.lseek(index_file, get_start_pos(filename), 0)
    os.write(index_file, str.encode('{} {} {} {} {}\n'.format(
        get_timestamp(filename),
        cryp,
        cryp,
        ' ' * len(cryp),
        filename)))
    os.close(index_file)


def add(filename, content):
    """
    Make a copy of file content and save it in .lgit database.

    @param filename: (str) The file name.
    @param exist: (bool) True - file exists.
                        False - file does not exist.
    """
    create_file(hash_sha1(content), content)
    update_index_add(hash_sha1(content), filename)


def lgit_add(filename):
    """
    Lgit add.

    @param filename: (str) The file name.
    """
    try:
        file = os.open(filename, os.O_RDONLY)
        content = os.read(file, os.stat(file).st_size)
    except PermissionError:
        print_permission_error(filename)
    add(filename, content)
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
            print("fatal: " + item + " '" + item +
                "' is outside repository")
        else:
            print("fatal: pathspec '" + item +
                "' did not match any files")


def get_dict_index_content():
    """
    Get the list of tracked files.

    @return: (dict) The list of tracked files.
    """
    tracked = {}
    with open('.lgit/index', 'r') as file:
        for line in file:
            filename = line.split()[-1]
            tracked[filename] = line
    return tracked


def update_index_rm(filename, tracked):
    """
    Update file information in the index file (rm).

    @param filename: (str) The file name.
    @param tracked: (dict) The list of tracked files.
    """
    if filename in tracked:
        del tracked[filename]
    with open('.lgit/index', 'w') as file:
        file.write(''.join(tracked.values()))


def lgit_rm(filename, tracked):
    """
    Lgit remove.

    @param filename: (str) The file name.
    @param tracked: (dict) The list of tracked files.
    """
    if os.path.exists(filename):
        os.unlink(filename)
    update_index_rm(filename, tracked)


def execute_lgit_rm(rm_list):
    tracked = get_dict_index_content()
    for item in rm_list:
        if os.path.isfile(item):
            lgit_rm(item, tracked)
        elif os.path.isdir(item):
            sub_list = get_sub_files_dir(item)
            execute_lgit_rm(sub_list)
        else:
            print("fatal: pathspec '" + item +
                "' did not match any files")


def execute_lgit_config(name):
    """Write author name to the config file."""
    config_file = open('.lgit/config', 'w+')
    config_file.write(name + '\n')
    config_file.close()


def execute_lgit_lsfiles():
    sub_list = get_sub_files_dir('.')
    for file in sorted(get_dict_index_content().keys()):
        if './' + file in sub_list:
            print(file)


def main():
    """Run the main program."""
    args = parse_arguments()
    if not have_command_error(args.command):
        if args.command == 'init':
            execute_lgit_init()
        elif args.command == 'add':
            if check_empty_files(args.files, args.command):
                execute_lgit_add(args.files)
        elif args.command == 'rm':
            if check_empty_files(args.files, args.command):
                execute_lgit_rm(args.files)
        elif args.command == 'config':
            execute_lgit_config(args.files[0])
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
