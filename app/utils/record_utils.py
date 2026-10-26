import hashlib
import math
import re
class RecordUtils:
    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    @staticmethod
    def literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    @staticmethod
    def codes(text, pattern):
        return sorted({m.group(0) for m in re.finditer(pattern, text)})
    @staticmethod
    def vector_valid(vector, dimensions):
        return (isinstance(vector, (list, tuple)) and dimensions > 0 and len(vector) == dimensions
                and all(isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x) for x in vector)
                and any(x != 0 for x in vector))
