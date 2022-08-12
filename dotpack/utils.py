from functools import wraps

def only_device(function):
    """
    https://python3-cookbook.readthedocs.io/zh_CN/latest/c09/p02_preserve_function_metadata_when_write_decorators.html

    @only_device
    def set_mode(self):
    """
    @wraps(function)
    def _only_device(*args, **kwargs):
        # self args[0].url
        if args[0]._ledpanel:
            result = function(*args, **kwargs)
            return result
        else:
            print("仅在硬件上运行, 不支持模拟器")
            return None

    return _only_device
