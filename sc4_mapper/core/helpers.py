import os

# FIXME: thats hack for missing dircache... not sure its needed
global_cache = {}


def cached_listdir(path):
    res = global_cache.get(path)
    if res is None:
        res = os.listdir(path)
        global_cache[path] = res
    return res


# FIXME: ugly?
class DlgStub:
    def __init__(self):
        pass

    def Update(self, x, y):
        pass
