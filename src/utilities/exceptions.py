import werkzeug.exceptions.HTTPException


class HTTPException(werkzeug.exceptions.HTTPException):
    __init__(self, description, code):
        self.code = code
        self.description = description

    def dump():
        return self.description, self.code
