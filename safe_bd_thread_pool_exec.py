from concurrent.futures import ThreadPoolExecutor
from django.db import connections


class SafeDBThreadPoolExecutor(ThreadPoolExecutor):
    def submit(self, fn, *args, **kwargs):
        def wrapped_fn(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            finally:
                connections.close_all()

        return super().submit(wrapped_fn, *args, **kwargs)
