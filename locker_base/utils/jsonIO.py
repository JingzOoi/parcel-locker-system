from os import replace
from os.path import splitext
from random import randint
from json import dump, load, decoder


class JsonIO():

    def save(self, filename, data):

        path, _ = splitext(filename)
        tmp_file = f"{path}.{randint(1000, 9999)}.tmp"

        with open(tmp_file, "w", encoding="utf-8") as f:
            dump(data, f, indent=4, sort_keys=True, separators=(',', ' : '))
        try:
            with open(tmp_file, 'r', encoding='utf-8') as f:
                data = load(f)
        except decoder.JSONDecodeError:
            print(f"[ERROR] [JSONIO] The integrity check for tmp file of {filename} has failed. Operation cancelled.")
            return False
        except Exception as e:
            print(f"[ERROR] [JSONIO] An issue has occured: {e} {e.args}")
            return False

        replace(tmp_file, filename)
        return True

    def load(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = load(f)
            return data
        except Exception as e:
            print(f"[ERROR] [JSONIO] An issue has occured: {e} {e.args}")
            return {}

    def is_valid(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                load(f)
            return True
        except (FileNotFoundError, decoder.JSONDecodeError):
            return False
        except Exception as e:
            print(f"[ERROR] [JSONIO] An issue has occured: {e} {e.args}")
            return False


jsonIO = JsonIO()
