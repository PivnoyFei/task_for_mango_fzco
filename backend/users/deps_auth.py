from fastapi.param_functions import Form


class OAuth2PasswordRequestForm:

    def __init__(
        self,
        username: str = Form(),
        password: str = Form(),
    ):
        self.username = username
        self.password = password
