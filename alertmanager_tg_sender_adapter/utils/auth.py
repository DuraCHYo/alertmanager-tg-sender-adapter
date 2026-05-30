import os

import requests


class Authorization:
    def __init__(
        self,
        username="",
        password="",
        headers={"Content-Type": "application/json"},
        timeout=10,
    ):
        self.username = os.getenv("XPLATFORM_USERNAME", "None")
        self.password = os.getenv("XPLATFORM_PASSWORD", "None")
        self.headers = headers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.auth = (self.username, self.password)

    def post(self, url, json, timeout):
        requests = self.session.post(url, json=json, timeout=timeout)
        return requests
