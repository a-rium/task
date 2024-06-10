import argparse
import sys
import os
import os.path
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
    context_directory = os.path.join(ROOT, 'context', name)
    if os.path.exists(context_directory):
        print(f'Context {context_directory} already exists.')
        return False
    return mkdir(context_directory, recursive=True)


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


def redact_task_step(context: TaskContext, task_name: str, description: str):
    task_directory = os.path.join(ROOT, 'context', context.name, task_name)
    if not os.path.exists(task_directory):
        print(f'Task "{task_name}" does not exist; create it first by using `task add {task_name} ...`')
        return

    steps = os.listdir(task_directory)
    if 'SOLVE.task' in steps:
        with open(os.path.join(task_directory, 'SOLVE.task'), 'w') as f:
            f.write(description)
    steps = [remove_suffix(step, '.task') for step in steps]
    steps = [int(step) for step in steps if step.isdigit()]
    next_step = str(max(steps)) if len(steps) > 0 else 'ADD'

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


def print_task_step(task_directory: str, step: str, max_step_width: int):
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

    print_task_step(task_directory, 'ADD', max_step_width)
    for step in inner_steps:
        print_task_step(task_directory, step, max_step_width)
    if 'SOLVE' in steps:
        print_task_step(task_directory, 'SOLVE', max_step_width)


def list_task(context: TaskContext, *, show_solved: bool, show_all: bool):
    context_directory = os.path.join(ROOT, 'context', context.name)

    tasks = os.listdir(context_directory)
    for task in tasks:

        task_directory = os.path.join(context_directory, task)
        steps = os.listdir(task_directory)
        steps = [remove_suffix(step, '.task') for step in steps]
        inner_steps = [int(step) for step in steps if step.isdigit()]

        solved = 'SOLVE' in steps
        if solved and not show_solved and not show_all:
            continue
        if not solved and show_solved and not show_all:
            continue

        print(f'TASK {task}')
        if not solved and len(inner_steps) > 0:
            last_step = str(max(inner_steps))
            max_step_width = max(len(last_step), len('ADD'), len('SOLVE'))
        else:
            max_step_width = max(len('ADD'), len('SOLVE'))
        print_task_step(task_directory, 'ADD', max_step_width)
        if solved:
            print_task_step(task_directory, 'SOLVE', max_step_width)
        elif len(inner_steps) > 0:
            last_step = str(max(inner_steps))
            print_task_step(task_directory, last_step, max_step_width)
        print()


def handle_mode_context(context: TaskContext):
    print_current_context(context)


def handle_mode_context_add(args):
    create_context(args.context_name)


def handle_mode_context_list(args):
    list_context()


def handle_mode_context_set(args, context: TaskContext):
    set_context(context, args.context_name)


def handle_mode_add(args, context: TaskContext):
    add_task(context, args.task_name, args.description)


def handle_mode_step(args, context: TaskContext):
    add_task_step(context, args.task_name, args.description)


def handle_mode_redact(args, context: TaskContext):
    redact_task_step(context, args.task_name, args.description)


def handle_mode_solve(args, context: TaskContext):
    solve_task(context, args.task_name, args.description)


def handle_mode_show(args, context: TaskContext):
    show_task(context, args.task_name)


def handle_mode_list(args, context: TaskContext):
    list_task(context, show_solved=args.show_solved, show_all=args.show_all)


def main() -> int:
    context = load_context()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    context_parser = subparsers.add_parser('context')
    context_parser.set_defaults(handle=lambda args: handle_mode_context(context))
    context_subparsers = context_parser.add_subparsers()

    context_add_parser = context_subparsers.add_parser('add')
    context_add_parser.add_argument('context_name')
    context_add_parser.set_defaults(handle=handle_mode_context_add)

    context_list_parser = context_subparsers.add_parser('list')
    context_list_parser.set_defaults(handle=handle_mode_context_list)

    context_set_parser = context_subparsers.add_parser('set')
    context_set_parser.add_argument('context_name')
    context_set_parser.set_defaults(handle=lambda args: handle_mode_context_set(args, context))

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('task_name')
    add_parser.add_argument('description')
    add_parser.set_defaults(handle=lambda args: handle_mode_add(args, context))

    step_parser = subparsers.add_parser('step')
    step_parser.add_argument('task_name')
    step_parser.add_argument('description')
    step_parser.set_defaults(handle=lambda args: handle_mode_step(args, context))

    redact_parser = subparsers.add_parser('redact')
    redact_parser.add_argument('task_name')
    redact_parser.add_argument('description')
    redact_parser.set_defaults(handle=lambda args: handle_mode_redact(args, context))

    solve_parser = subparsers.add_parser('solve')
    solve_parser.add_argument('task_name')
    solve_parser.add_argument('description')
    solve_parser.set_defaults(handle=lambda args: handle_mode_solve(args, context))

    show_parser = subparsers.add_parser('show')
    show_parser.add_argument('task_name')
    show_parser.set_defaults(handle=lambda args: handle_mode_show(args, context))

    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('-s', dest='show_solved', action='store_true')
    list_parser.add_argument('--solved', dest='show_solved', action='store_true')
    list_parser.add_argument('-a', dest='show_all', action='store_true')
    list_parser.add_argument('--all', dest='show_all', action='store_true')
    list_parser.set_defaults(handle=lambda args: handle_mode_list(args, context))

    args = parser.parse_args(sys.argv[1:])
    args.handle(args)

    save_context(context)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
