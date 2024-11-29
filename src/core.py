class ArgsError(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class InstTableError(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)