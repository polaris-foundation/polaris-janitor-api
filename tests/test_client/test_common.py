import httpx
from pytest_mock import MockFixture
from respx import MockRouter

from dhos_janitor_api.blueprint_api.client import common


class TestCommon:
    def test_log_if_deprecated(
        self, respx_mock: MockRouter, mocker: MockFixture
    ) -> None:
        mock_logger_warning = mocker.patch.object(common.logger, "warning")
        mock_response = respx_mock.get(url="http://dev.sensynehealth.com").mock(
            return_value=httpx.Response(
                status_code=200, headers={"Deprecation": "true"}
            )
        )

        common._log_if_deprecated(httpx.get("http://dev.sensynehealth.com"))

        assert mock_response.called
        mock_logger_warning.assert_called_once()

    def test_make_request(self, respx_mock: MockRouter, mocker: MockFixture) -> None:
        url = "http://dev.sensynehealth.com"
        mock_response = respx_mock.get(url=url).mock(
            return_value=httpx.Response(status_code=200)
        )

        client = httpx.Client()

        spy_client = mocker.spy(client, "request")

        common.make_request(client=client, method="get", url=url)

        assert mock_response.called
        spy_client.assert_called_once_with(
            "get", url, json=None, params=None, headers=None, timeout=60
        )
