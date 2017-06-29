class ResponseError(Exception):
    def __init__(self, url, message, status_code):
        self.url = url
        self.message = message
        self.status_code = status_code


class ClientError(ResponseError):
    pass


class ServiceError(ResponseError):
    pass
