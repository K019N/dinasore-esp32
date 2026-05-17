import os
import time

from utils.is_micropython import is_micropython


_log_path = None


def configure(filename=None):
    global _log_path

    if filename is not None:
        _log_path = filename
    elif is_micropython():
        _log_path = '/dinasore/resources/request_timing.log'
    else:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        _log_path = os.path.join(base_dir, 'resources', 'request_timing.log')

    _ensure_parent_dir(_log_path)
    _write_line('process_ms;total_ms')


def start_timer():
    if hasattr(time, 'ticks_ms'):
        return time.ticks_ms()
    return int(time.time() * 1000)


def elapsed_ms(start):
    now = start_timer()
    if hasattr(time, 'ticks_diff'):
        return time.ticks_diff(now, start)
    return now - start


def log_request(client, data, response, process_ms, total_ms, status='OK', error=''):
    if _log_path is None:
        configure()

    line = '{0};{1}'.format(process_ms, total_ms)
    _write_line(line)


def _write_line(line):
    try:
        with open(_log_path, 'a') as file:
            file.write(line)
            file.write('\n')
    except Exception:
        pass


def _ensure_parent_dir(path):
    parent = path.replace('\\', '/').rsplit('/', 1)[0]
    if not parent:
        return
    try:
        os.listdir(parent)
    except OSError:
        _makedirs(parent)


def _makedirs(path):
    normalized = path.replace('\\', '/')
    prefix = ''
    parts = normalized.split('/')

    if normalized.startswith('/'):
        prefix = '/'

    current = prefix
    for part in parts:
        if not part:
            continue
        if current in ('', '/'):
            current = current + part
        else:
            current = current + '/' + part
        try:
            os.mkdir(current)
        except OSError:
            pass
