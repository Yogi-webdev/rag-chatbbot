class Document:

    def __init__(self, filename, file_type, text):
        self.filename = filename
        self.file_type = file_type
        self.text = text


class Chunk:

    def __init__(self, filename, chunk_id, text, embedding=None):
        self.filename = filename
        self.chunk_id = chunk_id
        self.text = text
        self.embedding = embedding