import argparse
import sys
import os
import os.path


ROOT = os.path.expanduser(os.path.join('~', '.task'))
CONTEXT_CONFIGURATION = os.path.join(ROOT, '.conf', '.context')


class TaskContext:
    name: str

    def __init__(self):
        self.name = None


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


def load_context() -> TaskContext:
    configuration = TaskContext()
    if os.path.exists(CONTEXT_CONFIGURATION):
        for line in open(CONTEXT_CONFIGURATION):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if key in configuration.__dict__:
                configuration.__dict__[key] = value
    return configuration


def save_context(context: TaskContext):
    if not os.path.exists(CONTEXT_CONFIGURATION):
        dirpath, _ = os.path.split(CONTEXT_CONFIGURATION)
        mkdir(dirpath, recursive=True)
    with open(CONTEXT_CONFIGURATION, 'w') as f:
        for key, value in context.__dict__.items():
            if value is not None:
                f.write(f'{key}: {value}\n')


def print_current_context(context: TaskContext):
    if context.name is None:
        print('No context selected; set it using `task context set <context-name>`')
    else:
        print(context.name)


def create_context(name: str) -> bool:
    return mkdir(os.path.join(ROOT, 'context', name), recursive=True)


def list_context():
    for context in os.listdir(os.path.join(ROOT, 'context')):
        print(context)


def set_context(context: TaskContext, context_name: str):
    if os.path.exists(os.path.join(ROOT, 'context', context_name)):
        context.name = context_name
    else:
        print(f'Could not find context {context_name}; create it first using `task context add {context_name}`')


def add_task(context: TaskContext, task_name: str, description: str):
    task_directory = os.path.join(ROOT, 'context', context.name, task_name)
    if os.path.exists(task_directory):
        print(f'Task "{task_name}" already exists; view it using `task show {task_name} ...` or add a new step by using `task step {task_name} ...`')
        return

    mkdir(task_directory)
    with open(os.path.join(task_directory, 'ADD.task'), 'w') as f:
        f.write(description)


def main() -> int:
    context = load_context()

    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('ignore', nargs='*')

    args = parser.parse_args(sys.argv[1:])
    if args.mode == 'context':
        parser = argparse.ArgumentParser()
        parser.add_argument('mode', nargs='?')
        parser.add_argument('ignore', nargs='*')

        args = parser.parse_args(sys.argv[2:])

        if args.mode is None:
            print_current_context(context)
        elif args.mode == 'add':
            parser = argparse.ArgumentParser()
            parser.add_argument('context_name')
            parser.add_argument('ignore', nargs='*')

            args = parser.parse_args(sys.argv[3:])
            create_context(args.context_name)
        elif args.mode == 'list':
            list_context()
        elif args.mode == 'set':
            parser = argparse.ArgumentParser()
            parser.add_argument('context_name')
            parser.add_argument('ignore', nargs='*')

            args = parser.parse_args(sys.argv[3:])
            set_context(context, args.context_name)
    elif args.mode == 'add':
        parser = argparse.ArgumentParser()
        parser.add_argument('task_name')
        parser.add_argument('description')

        args = parser.parse_args(sys.argv[2:])
        add_task(context, args.task_name, args.description)


    save_context(context)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
