
class FakeUpload:
    def __init__(self, name, data: bytes):
        self.name = name
        self._data = data
        self._read_once = False

    def read(self):
        # mimic streamlit UploadedFile: returns bytes once unless seek(0) is used by caller
        if self._read_once:
            return b""
        self._read_once = True
        return self._data

    def seek(self, pos):
        # reset read flag to allow re-read
        if pos == 0:
            self._read_once = False
