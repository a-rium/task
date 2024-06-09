import argparse
import sys
import os
import os.path


ROOT = os.path.expanduser(os.path.join('~', '.task'))


def wrapped_os_mkdir(dirpath: str) -> bool:
    created = False
    try:
        os.mkdir(dirpath)
        created = True
    except (FileExistsError, FileNotFoundError):
        pass
    return created


def mkdir(dirpath: str, *, recursive=False) -> bool:
    created = False
    if recursive:
        dirtree, directory = os.path.split(dirpath)
        if dirtree != os.path.sep:
            mkdir(dirtree, recursive=recursive)
        created = wrapped_os_mkdir(dirpath)
    else:
        created = wrapped_os_mkdir(dirpath)
    return created


def create_context(name: str) -> bool:
    return mkdir(os.path.join(ROOT, 'context', name), recursive=True)


def list_context():
    for context in os.listdir(os.path.join(ROOT, 'context')):
        print(context)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('ignore', nargs='*')

    args = parser.parse_args(sys.argv[1:])
    if args.mode == 'context':
        parser = argparse.ArgumentParser()
        parser.add_argument('mode')
        parser.add_argument('ignore', nargs='*')

        args = parser.parse_args(sys.argv[2:])

        if args.mode == 'add':
            parser = argparse.ArgumentParser()
            parser.add_argument('context_name')
            parser.add_argument('ignore', nargs='*')

            args = parser.parse_args(sys.argv[3:])
            create_context(args.context_name)
        elif args.mode == 'list':
            list_context()


    return 0


if __name__ == '__main__':
    raise SystemExit(main())
