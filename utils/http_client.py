import requests
from utils.logger import logger


class HttpClient:
    """HTTP 请求客户端封装"""

    def __init__(self, base_url: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def request(
        self,
        method: str,
        path: str,
        headers: dict = None,
        params: dict = None,
        json_data: dict = None,
    ) -> requests.Response:
        """
        发送 HTTP 请求

        Args:
            method: 请求方法 (GET/POST/PUT/DELETE/PATCH)
            path: 请求路径
            headers: 请求头
            params: URL 查询参数
            json_data: JSON 请求体

        Returns:
            requests.Response 响应对象
        """
        url = f"{self.base_url}/{path.lstrip('/')}" if self.base_url else path
        method = method.upper()

        logger.info(f"请求: {method} {url}")
        if params:
            logger.info(f"Query Params: {params}")
        if json_data:
            logger.info(f"Body: {json_data}")

        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json_data,
            timeout=self.timeout,
        )

        logger.info(f"响应状态码: {response.status_code}")
        try:
            logger.info(f"响应内容: {response.json()}")
        except Exception:
            logger.info(f"响应内容: {response.text[:200]}")

        return response

    def close(self):
        self.session.close()
