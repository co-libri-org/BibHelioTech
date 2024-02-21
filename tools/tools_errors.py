class ToolsError(Exception):
    """BHT tools base exception"""

    def __init__(self, message="BHT Tools Error"):
        self.message = message
        super().__init__(self.message)


class ToolsValueError(ToolsError):
    pass

class ToolsFileError(ToolsError):
    pass
