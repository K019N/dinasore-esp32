import _thread

from utils.is_micropython import is_micropython


CLIENT_THREAD_STACK = 8192
FB_THREAD_STACK = 8192


def set_thread_stack_size(size):
    if not is_micropython():
        return

    try:
        _thread.stack_size(size)
    except Exception:
        pass
