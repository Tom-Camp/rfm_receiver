import msgpack
import pytest
import requests

from rfm_receiver.receive import LoraReceiver


@pytest.fixture
def receiver(mocker):
    """Return a LoraReceiver with all hardware calls mocked out."""
    mocker.patch("rfm_receiver.receive.digitalio.DigitalInOut")
    mocker.patch("rfm_receiver.receive.busio.SPI")
    mocker.patch("rfm_receiver.receive.adafruit_rfm9x.RFM9x")
    return LoraReceiver()


# ---------------------------------------------------------------------------
# receive_data
# ---------------------------------------------------------------------------


class TestReceiveData:
    def test_calls_process_packet_when_packet_received(self, receiver, mocker):
        packet = msgpack.packb({"sender_id": "node1", "data": {}})
        receiver.rfm9x.receive.return_value = packet
        mock_process = mocker.patch.object(receiver, "_process_packet")

        receiver.receive_data()

        mock_process.assert_called_once_with(packet=packet)

    def test_does_not_call_process_packet_when_no_packet(self, receiver, mocker):
        receiver.rfm9x.receive.return_value = None
        mock_process = mocker.patch.object(receiver, "_process_packet")

        receiver.receive_data()

        mock_process.assert_not_called()

    def test_logs_error_on_ioerror(self, receiver, mocker):
        receiver.rfm9x.receive.side_effect = IOError("SPI failure")
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        receiver.receive_data()

        mock_logger.error.assert_called_once()
        assert "SPI failure" in mock_logger.error.call_args[0][0]

    def test_passes_timeout_to_receive(self, receiver):
        receiver.rfm9x.receive.return_value = None
        receiver.receive_data()
        receiver.rfm9x.receive.assert_called_once_with(
            with_ack=True, timeout=receiver.receive_timeout
        )


# ---------------------------------------------------------------------------
# _process_packet
# ---------------------------------------------------------------------------


class TestProcessPacket:
    def test_valid_packet_calls_post_data(self, receiver, mocker):
        payload = {"sender_id": "node1", "data": {"device_id": "d1", "api_key": "k", "data": {}}}
        packet = msgpack.packb(payload)
        mock_post = mocker.patch.object(receiver, "_post_data")

        receiver._process_packet(packet)

        mock_post.assert_called_once_with(packet_data=payload["data"])

    def test_non_dict_packet_logs_error_and_does_not_call_post_data(self, receiver, mocker):
        packet = msgpack.packb([1, 2, 3])
        mock_post = mocker.patch.object(receiver, "_post_data")
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        receiver._process_packet(packet)

        mock_post.assert_not_called()
        mock_logger.error.assert_called_once()

    def test_malformed_packet_logs_unpack_error(self, receiver, mocker):
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        receiver._process_packet(b"\xff\xfe\xfd")

        mock_logger.error.assert_called_once()

    def test_logs_sender_id(self, receiver, mocker):
        payload = {"sender_id": "sensor-42", "data": {}}
        packet = msgpack.packb(payload)
        mocker.patch.object(receiver, "_post_data")
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        receiver._process_packet(packet)

        mock_logger.info.assert_called_once()
        assert "sensor-42" in mock_logger.info.call_args[0][0]


# ---------------------------------------------------------------------------
# _post_data
# ---------------------------------------------------------------------------


class TestPostData:
    def _make_packet_data(self, device_id="dev1", api_key="key123", data=None):
        return {
            "device_id": device_id,
            "api_key": api_key,
            "data": data or {"temp": 22.5},
        }

    def test_posts_to_api_with_correct_headers(self, mocker, monkeypatch):
        monkeypatch.setenv("API_URL", "http://example.com/api")
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_post = mocker.patch("rfm_receiver.receive.requests.post", return_value=mock_response)

        LoraReceiver._post_data(self._make_packet_data())

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["headers"]["X-API-KEY"] == "key123"
        assert kwargs["headers"]["X-Device-Id"] == "dev1"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"] == {"temp": 22.5}

    def test_missing_api_url_logs_error_and_does_not_post(self, mocker, monkeypatch):
        monkeypatch.delenv("API_URL", raising=False)
        mock_post = mocker.patch("rfm_receiver.receive.requests.post")
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        LoraReceiver._post_data(self._make_packet_data())

        mock_post.assert_not_called()
        mock_logger.error.assert_called_once()

    def test_request_exception_logs_error(self, mocker, monkeypatch):
        monkeypatch.setenv("API_URL", "http://example.com/api")
        mocker.patch(
            "rfm_receiver.receive.requests.post",
            side_effect=requests.exceptions.ConnectionError("unreachable"),
        )
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        LoraReceiver._post_data(self._make_packet_data())

        mock_logger.error.assert_called_once()

    def test_http_error_logs_error(self, mocker, monkeypatch):
        monkeypatch.setenv("API_URL", "http://example.com/api")
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mocker.patch("rfm_receiver.receive.requests.post", return_value=mock_response)
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        LoraReceiver._post_data(self._make_packet_data())

        mock_logger.error.assert_called_once()

    def test_logs_status_code_on_success(self, mocker, monkeypatch):
        monkeypatch.setenv("API_URL", "http://example.com/api")
        mock_response = mocker.MagicMock()
        mock_response.status_code = 201
        mocker.patch("rfm_receiver.receive.requests.post", return_value=mock_response)
        mock_logger = mocker.patch("rfm_receiver.receive.logger")

        LoraReceiver._post_data(self._make_packet_data())

        mock_logger.info.assert_called_once()
        assert "201" in mock_logger.info.call_args[0][0]
