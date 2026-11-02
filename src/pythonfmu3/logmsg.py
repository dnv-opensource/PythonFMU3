class LogMsg:
    def __init__(self, status: int, category: str, msg: str, debug: bool):
        self.status = status
        self.category = category
        self.msg = msg
        self.debug = debug

    def __str__(self) -> str:
        return f"LogMsg(status={self.status}, category={self.category}, msg={self.msg}, debug={self.debug}"
