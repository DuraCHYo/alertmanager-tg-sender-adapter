import os

import requests
from requests import Response


class Authorization:
    def __init__(
        self,
        username: str = "",
        password: str = "",
        timeout: int = 15,
    ) -> None:
        self.username = os.getenv("XPLATFORM_USERNAME", "None")
        self.password = os.getenv("XPLATFORM_PASSWORD", "None")
        self.timeout = timeout

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def post(
        self,
        url: str,
        json: dict,
        timeout: int | None = None,
    ) -> Response:
        return self.session.post(url, json=json, timeout=timeout or self.timeout)

    def image_post(
        self,
        url: str,
        chat_id: int,
        text: str,
        screenshot_path: str,
        timeout: int | None = None,
    ) -> Response:
        with open(screenshot_path, "rb") as f:
            files = {
                "imageFiles": (
                    os.path.basename(screenshot_path),
                    f,
                    "image/png",
                )
            }

            data = {
                "chatId": chat_id,
                "text": text,
            }

            return self.session.post(
                url,
                data=data,
                files=files,
                timeout=timeout or self.timeout,
            )
