# TODO: rewrite any WEB to BHT
class WebError(Exception):
    """BHT pipeline base exception"""

    def __init__(self, message="BHT Error"):
        self.message = message
        super().__init__(self.message)


class PdfFileError(WebError):
    """File or Dir path error"""

    pass


class WebPathError(WebError):
    """File or Dir path error"""

    pass


class WebResultError(WebError):
    """Result error"""

    pass


class IstexError(Exception):
    def __init__(self, message="ISTEX Error"):
        self.message = message
        super().__init__(self.message)


class IstexParamError(IstexError):
    pass
