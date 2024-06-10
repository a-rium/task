import argparse
import sys
import os
import os.path
import string
import dataclasses


ROOT = os.path.expanduser(os.path.join('~', '.task'))
CONTEXT_CONFIGURATION = os.path.join(ROOT, '.conf', '.context')


class TaskContext:
    name: str

    def __init__(self):
        self.name = None


@dataclasses.dataclass
class TaskStep:
    description: str


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


def remove_suffix(text: str, suffix: str) -> bool:
    if len(text) == 0:
        return text
    idx = text.rfind(suffix)
    if idx == len(text) - len(suffix):
        return text[:-len(suffix)]
    return text


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


def add_task_step(context: TaskContext, task_name: str, description: str):
    task_directory = os.path.join(ROOT, 'context', context.name, task_name)
    if not os.path.exists(task_directory):
        print(f'Task "{task_name}" does not exist; create it first by using `task add {task_name} ...`')
        return

    steps = os.listdir(task_directory)
    if 'SOLVE.task' in steps:
        print(f'Task "{task_name}" has been already marked as solved.')
    steps = [remove_suffix(step, '.task') for step in steps]
    steps = [int(step) for step in steps if step.isdigit()]
    next_step = max(steps) + 1 if len(steps) > 0 else 1

    with open(os.path.join(task_directory, f'{next_step}.task'), 'w') as f:
        f.write(description)


def solve_task(context: TaskContext, task_name: str, description: str):
    task_directory = os.path.join(ROOT, 'context', context.name, task_name)
    if not os.path.exists(task_directory):
        print(f'Task "{task_name}" does not exist; create it first by using `task add {task_name} ...`')
        return

    solve_step = os.path.join(task_directory, 'SOLVE.task')
    if os.path.exists(solve_step):
        print(f'Task "{task_name}" has been already marked as solved.')
        return

    with open(solve_step, 'w') as f:
        f.write(description)


def read_task_step(task_directory: str, step: str) -> TaskStep:
    with open(os.path.join(task_directory, f'{step}.task'), 'r') as f:
        description = f.read()
    return TaskStep(description=description)


def print_task(task_directory: str, step: str, max_step_width: int):
    task_step = read_task_step(task_directory, step)
    print(f'{step.rjust(max_step_width, " ")}. {task_step.description}')


def show_task(context: TaskContext, task_name: str):
    task_directory = os.path.join(ROOT, 'context', context.name, task_name)
    if not os.path.exists(task_directory):
        print(f'Task "{task_name}" does not exist; create it first by using `task add {task_name} ...`')
        return

    steps = os.listdir(task_directory)
    steps = [remove_suffix(step, '.task') for step in steps]
    inner_steps = [step for step in steps if step.isdigit()]
    max_step_width = max(*(len(step) for step in inner_steps), len('ADD'), len('SOLVE'))

    print_task(task_directory, 'ADD', max_step_width)
    for step in inner_steps:
        print_task(task_directory, step, max_step_width)
    if 'SOLVE' in steps:
        print_task(task_directory, 'SOLVE', max_step_width)


def list_task(context: TaskContext):
    context_directory = os.path.join(ROOT, 'context', context.name)

    tasks = os.listdir(context_directory)
    for task in tasks:
        print(f'TASK {task}')

        task_directory = os.path.join(context_directory, task)
        steps = os.listdir(task_directory)
        steps = [remove_suffix(step, '.task') for step in steps]
        inner_steps = [int(step) for step in steps if step.isdigit()]

        solved = 'SOLVE' in steps
        if not solved and len(inner_steps) > 0:
            last_step = str(max(inner_steps))
            max_step_width = max(len(last_step), len('ADD'), len('SOLVE'))
        else:
            max_step_width = max(len('ADD'), len('SOLVE'))
        print_task(task_directory, 'ADD', max_step_width)
        if solved:
            print_task(task_directory, 'SOLVE', max_step_width)
        elif len(inner_steps) > 0:
            last_step = str(max(inner_steps))
            print_task(task_directory, last_step, max_step_width)
        print()


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
    elif args.mode == 'step':
        parser = argparse.ArgumentParser()
        parser.add_argument('task_name')
        parser.add_argument('description')

        args = parser.parse_args(sys.argv[2:])
        add_task_step(context, args.task_name, args.description)
    elif args.mode == 'solve':
        parser = argparse.ArgumentParser()
        parser.add_argument('task_name')
        parser.add_argument('description')

        args = parser.parse_args(sys.argv[2:])
        solve_task(context, args.task_name, args.description)
    elif args.mode == 'show':
        parser = argparse.ArgumentParser()
        parser.add_argument('task_name')

        args = parser.parse_args(sys.argv[2:])
        show_task(context, args.task_name)
    elif args.mode == 'list':
        list_task(context)

    save_context(context)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
