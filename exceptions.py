class NotTwoHundred(Exception):
    pass


class NotList(Exception):
    pass


class NotSend(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'NotSend: {0} '.format(self.message)
        else:
            return 'Сработала ошибка NotSend'


class NotResponse(Exception):
    pass


class NotStatus(Exception):
    pass
