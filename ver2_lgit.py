#!/usr/bin/env python3
from argparse import ArgumentParser
from os import getcwd, mkdir, environ, walk, unlink, listdir
from os.path import exists, isdir, isfile, dirname, join, getmtime
from hashlib import sha1
from datetime import datetime
from time import time


def parse_arguments():
    """
    Parse command line strings into Python objects.

    @return: (namespace) An object to take the attributes.
    """
    parser = ArgumentParser(
        usage='./lgit.py <command> [<args>]',
        description='A lightweight version of git')
    sub_parsers = parser.add_subparsers(
        dest='command',
        metavar='command',
        help='lgit command')
    # lgit init
    init_parser = sub_parsers.add_parser('init')
    # lgit add files
    add_parser = sub_parsers.add_parser('add')
    add_parser.add_argument('files', nargs='+')
    # lgit rm files
    remove_parser = sub_parsers.add_parser('rm')
    remove_parser.add_argument('files', nargs='+')
    # lgit config --author name
    config_parser = sub_parsers.add_parser('config')
    config_parser.add_argument('--author', required=True)
    # lgit commit -m message
    commit_parser = sub_parsers.add_parser('commit')
    commit_parser.add_argument('-m', dest='message', required=True)
    # lgit status
    status_parser = sub_parsers.add_parser('status')
    # lgit log
    log_parser = sub_parsers.add_parser('log')
    # lgit ls-file
    list_files_parser = sub_parsers.add_parser('ls-files')
    return parser.parse_args()


def get_lgit_directory():
    """Get the closest directory that has a .lgit directory in it."""
    path = getcwd()
    while path != '/':
        if isdir(path + '/.lgit'):
            return path
        path = dirname(path)
    return None


def print_repo_exist_error():
    print('fatal: not a git repository (or any of the parent directories)')
    exit()


def check_repo_exist():
    """Check the repository was initialize."""
    if get_lgit_directory():
        return True
    return False


def create_dir(path):
    if not exists(path):
        try:
            mkdir(path)
        except FileExistsError:
            pass


def create_file(path):
    try:
        with open(path, 'w+'):
            pass
    except PermissionError:
        pass


def write_logname_config():
    try:
        file = open(get_lgit_directory() + '/.lgit/config', 'w+')
        file.write(environ['LOGNAME'] + '\n')
        file.close()
    except PermissionError:
        pass


def create_repo():
    dirs = ['.lgit',
            '.lgit/objects',
            '.lgit/commits',
            '.lgit/snapshots']
    files = ['.lgit/index',
             '.lgit/config']
    for dir in dirs:
        create_dir(dir)
    for file in files:
        create_file(file)
    write_logname_config()


def lgit_init():
    """Initialize version control in the current directory."""
    if check_repo_exist():
        print('Git repository already initialized.')
    else:
        create_repo()


def get_all_files(dir):
    """Get all files in current directory and sub-directories."""
    sub_files = []
    for root, _, files in walk(dir):
        for file in files:
            if '.lgit/' not in join(root, file):
                sub_files.append(join(root, file))
    return sub_files


def print_pathspec_error(path):
    print("fatal: pathspec '" + path + "' did not match any files")
    exit()


def get_file_paths(paths):
    if '.' in paths or '*' in paths:
        return sorted([file[2:] for file in get_all_files('.')])
    files = []
    for path in paths:
        if isfile(path) and '.lgit/' not in path:
            files.append(path)
        elif isdir(path):
            files += get_all_files(path)
        else:
            print_pathspec_error(path)
    return sorted(files)


def hash_sha1(path):
    """Hash content to SHA1."""
    try:
        with open(path, 'r') as file:
            return sha1(file.read().encode()).hexdigest()
    except (PermissionError, FileNotFoundError):
        pass


def get_content(path):
    try:
        with open(path, 'r') as file:
            return file.read()
    except (PermissionError, FileNotFoundError):
        pass


def make_copy(src, dest):
    try:
        with open(dest, 'w+') as file:
            file.write(get_content(src))
    except PermissionError:
        pass


def add_file(path, sha):
    create_dir(get_lgit_directory() + '/.lgit/objects/' + sha[:2])
    make_copy(
        path,
        get_lgit_directory() + '/.lgit/objects/' + sha[:2] + '/' + sha[2:])


def get_timestamp(path):
    """Get timestamp of the file."""
    timestamp = datetime.fromtimestamp(getmtime(path))
    return timestamp.strftime('%Y%m%d%H%M%S')


def get_index_dict():
    index = {}
    try:
        with open(get_lgit_directory() + '/.lgit/index', 'r') as file:
            for line in file:
                index[line[:-1].split()[-1]] = line
    except PermissionError:
        pass
    return index


def create_info(path):
    return '{} {} {} {} {}\n'.format(
        get_timestamp(path),
        hash_sha1(path),
        hash_sha1(path),
        ' ' * 40,
        path)


def change_info(index, path):
    state = index[path]
    index[path] = '{} {} {} {} {}\n'.format(
        get_timestamp(path),
        hash_sha1(path),
        hash_sha1(path),
        state[97:137],
        path)


def update_index_file(index):
    try:
        with open(get_lgit_directory() + '/.lgit/index', 'w+') as file:
            file.write(''.join(index.values()))
    except PermissionError:
        pass


def lgit_add(paths):
    """Store a copy of the file content in the lgit database."""
    index = get_index_dict()
    for path in get_file_paths(paths):
        add_file(path, hash_sha1(path))
        if path not in index.keys():
            index[path] = create_info(path)
        else:
            change_info(index, path)
    update_index_file(index)


def print_recursive_error(path):
    print("fatal: not removing '" + path + "' recursively")
    exit()


def lgit_remove(paths):
    """Remove files from the working directory and the index."""
    index = get_index_dict()
    for path in paths:
        if isfile(path) and path in index.keys():
            unlink(path)
            del index[path]
        elif isdir(path):
            print_recursive_error(path)
        else:
            print_pathspec_error(path)
    update_index_file(index)


def lgit_config(author):
    """Set a user for authoring the commits."""
    try:
        file = open(get_lgit_directory() + '/.lgit/config', 'w+')
        file.write(author + '\n')
        file.close()
    except PermissionError:
        pass


def create_commit_file(message, tst_1, tst_2):
    author = get_content(get_lgit_directory() + '/.lgit/config').strip('\n')
    if not author:
        exit()
    try:
        with open(get_lgit_directory() + '/.lgit/commits/' + tst_1,
                  'w+') as file:
            file.write('{}\n{}\n\n{}\n'.format(author, tst_2, message))
    except PermissionError:
        pass


def create_snap_file(index, tst_1):
    for path, state in index.items():
        index[path] = '{} {} {} {} {}\n'.format(
            get_timestamp(path),
            hash_sha1(path),
            state[56:96],
            state[56:96],
            path)
        with open(get_lgit_directory() + '/.lgit/snapshots/' + tst_1,
                  'a+') as file:
            file.write(state[56:96] + ' ' + path + '\n')


def lgit_commit(message):
    """create a commit with the changes currently staged."""
    cur_time = datetime.fromtimestamp(time())
    create_commit_file(
        message,
        cur_time.strftime('%Y%m%d%H%M%S.%f'),
        cur_time.strftime('%Y%m%d%H%M%S'))
    index = get_index_dict()
    create_snap_file(index, cur_time.strftime('%Y%m%d%H%M%S.%f'))
    update_index_file(index)


def print_on_branch():
    print('On branch master\n')
    if not listdir(get_lgit_directory() + '/.lgit/commits'):
        print('No commits yet\n')


def get_status_paths_list():
    index = get_index_dict()
    to_be_committed, not_staged_for_commit = [], []
    for path, state in index.items():
        index[path] = '{} {} {} {} {}\n'.format(
            get_timestamp(path),
            hash_sha1(path),
            state[56:96],
            state[97:137],
            path)
        if state[56:96] != state[97:137]:
            to_be_committed.append(path)
        if state[56:96] != hash_sha1(path):
            not_staged_for_commit.append(path)
    update_index_file(index)
    return [to_be_committed, not_staged_for_commit]


def print_to_be_committed(paths):
    if paths:
        print('Changes to be committed:')
        print('  (use "./lgit.py reset HEAD ..." to unstage)')
        print('\n\t modified: %s\n' % '\n\t modified: '.join(paths))


def print_not_staged_for_commit(paths):
    if paths:
        print('Changes not staged for commit:')
        print('  (use "./lgit.py add ..." to update what will be committed)')
        print('  (use "./lgit.py checkout -- ..." '
              'to discard changes in working directory)')
        print('\n\t modified: %s\n' % '\n\t modified: '.join(paths))


def get_untracked_files():
    untracked_files = []
    tracked_files = get_index_dict().keys()
    for path in sorted([file[2:] for file in get_all_files('.')]):
        if path not in tracked_files:
            untracked_files.append(path)
    return untracked_files


def print_untracked_files(paths):
    if paths:
        print('Untracked files:')
        print('  (use "./lgit.py add <file>..." '
              'to include in what will be committed)')
        print('\n\t%s\n' % '\n\t'.join(paths))
        print('nothing added to commit but untracked files present '
              '(use "./lgit.py add" to track)')


def lgit_status():
    """
    Update the index with the content of the working directory.
    Display the status of tracked/untracked files.
    """
    print_on_branch()
    paths_list = get_status_paths_list()
    print_to_be_committed(paths_list[0])
    print_not_staged_for_commit(paths_list[1])
    print_untracked_files(get_untracked_files())


def get_datetime(filename):
    dt = datetime(
        year=int(filename[0:4]),
        month=int(filename[4:6]),
        day=int(filename[6:8]),
        hour=int(filename[8:10]),
        minute=int(filename[10:12]),
        second=int(filename[12:14]))
    return dt.strftime('%a %b %d %H:%M:%S %Y')


def print_commit_history(filename):
    try:
        with open(get_lgit_directory() + '/.lgit/commits/' + filename,
                  'r') as file:
            content = file.read().split()
            print('commit ' + filename)
            print('Author: ' + content[0])
            print('Date: ' + get_datetime(filename))
            print('\n\t' + content[-1])
    except (PermissionError, FileNotFoundError):
        pass


def lgit_log():
    """Show the commit history."""
    commit_files = sorted(listdir(get_lgit_directory() + '/.lgit/commits'),
                          reverse=True)
    for file in commit_files:
        print_commit_history(file)
        if file != commit_files[-1]:
            print('\n')


def lgit_ls_files():
    """
    List all the files currently tracked in the index,
    relative to the current directory.
    """
    for file in [file[2:] for file in get_all_files('.')]:
        for path in get_index_dict().keys():
            if path.endswith(file):
                print(file)


def main():
    args = parse_arguments()
    if args.command == 'init':
        lgit_init()
    elif check_repo_exist():
        if args.command == 'add':
            lgit_add(args.files)
        elif args.command == 'rm':
            lgit_remove(args.files)
        elif args.command == 'config':
            lgit_config(args.author)
        elif args.command == 'commit':
            lgit_commit(args.message)
        elif args.command == 'status':
            lgit_status()
        elif args.command == 'log':
            lgit_log()
        elif args.command == 'ls-files':
            lgit_ls_files()
    else:
        print_repo_exist_error()


if __name__ == '__main__':
    main()
