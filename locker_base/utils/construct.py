from os.path import join
from typing import Iterable


def construct_path(*args) -> str:
    path_name = ""
    for a in args:
        path_name = join(path_name, a)
    return path_name
