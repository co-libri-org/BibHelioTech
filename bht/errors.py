class BhtError(Exception):
    """BHT pipeline base exception"""

    def __init__(self, message="BHT Error"):
        self.message = message
        super().__init__(self.message)


class BhtPipelineError(BhtError):
    """Pipeline error"""

    pass


class BhtPathError(BhtError):
    """File or Dir path error"""

    pass


class BhtResultError(BhtError):
    """Result error"""

    pass


class BhtCsvError(BhtError):
    """Result error"""

    pass
