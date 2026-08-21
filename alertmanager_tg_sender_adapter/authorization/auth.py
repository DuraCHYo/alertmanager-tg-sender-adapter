import os

import requests
from dotenv import load_dotenv
from requests import Response
from urllib3 import disable_warnings

load_dotenv()

import logging

logger = logging.getLogger(__name__)
verify_ssl = os.getenv("VERIFY_SSL", "true").lower() != "false"

if not verify_ssl:
    disable_warnings()
    logger.warning("SSL отключен")


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
        """

        Args:
            url: os.getenv("XPLATFORM_ADDRESS")
            json: "alert body"
            timeout: 15

        Returns:
            Response()
        """
        return self.session.post(
            url, json=json, timeout=timeout or self.timeout, verify=verify_ssl
        )

    def image_post(
        self,
        url: str,
        chat_id: int,
        text: str,
        screenshot_path: str,
        timeout: int | None = None,
    ) -> Response:
        """

        Args:
            url: os.getenv("XPLATFORM_ADDRESS")
            chat_id: "-100..."
            text: "Alert body"
            screenshot_path: "Pathlib"
            timeout: 15

        Returns:
            Response()
        """
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
                verify=verify_ssl,
            )
