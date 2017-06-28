# class ExceptionReturn(Exception):
#     def __init__(self, message, status_code):
#         self.message = message
#         self.status_code = status_code


class ClientError(Exception):
    pass


class ServiceError(Exception):
    pass
