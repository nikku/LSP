from .typing import Any
import traceback
import inspect
import sublime


log_debug = False


def set_debug_logging(logging_enabled: bool) -> None:
    global log_debug
    log_debug = logging_enabled


def get_log_debug() -> bool:
    global log_debug
    return log_debug


def debug(message: str) -> None:
    """Print args to the console if the "debug" setting is True."""
    if log_debug:
        printf(message)


def trace() -> None:
    current_frame = inspect.currentframe()
    if current_frame is None:
        debug("TRACE (unknown frame)")
        return
    previous_frame = current_frame.f_back
    file_name, line_number, function_name, _, __ = inspect.getframeinfo(previous_frame)  # type: ignore
    file_name = file_name[len(sublime.packages_path()) + len("/LSP/"):]
    debug("TRACE {0:<32} {1}:{2}".format(function_name, file_name, line_number))


def exception_log(message: str, ex: Exception) -> None:
    print(message)
    ex_traceback = ex.__traceback__
    print(''.join(traceback.format_exception(ex.__class__, ex, ex_traceback)))


def printf(message: str, prefix: str = 'LSP') -> None:
    from .panels import log_server_message
    """Print args to the console, prefixed by the plugin name."""
    log_server_message(sublime.active_window(), prefix + ":", message=message)
