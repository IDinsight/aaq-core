import pytest
from fastapi.testclient import TestClient


class TestTranscribeAudioEndpoint:

    @pytest.mark.parametrize(
        "file_path, expected_keywords, expected_language, expected_status_code",
        [
            (
                "tests/data/test.mp3",
                ["STT", "test", "external"],
                "en",
                200,
            ),
        ],
    )
    def test_transcribe_audio_success(
        self,
        file_path: str,
        expected_keywords: str,
        expected_language: str,
        expected_status_code: int,
        client: TestClient,
    ) -> None:

        response = client.post("/transcribe", json={"file_path": file_path})
        assert response.status_code == expected_status_code
        assert response.json()["text"] != ""
        for keyword in expected_keywords:
            assert keyword in response.json()["text"]
        assert response.json()["language"] == expected_language

    @pytest.mark.parametrize(
        "file_path, expected_status_code, expected_detail",
        [
            (
                "tests/data/non_existent_audio.wav",
                404,
                "File not found.",
            ),
            # (
            #     "tests/data/invalid_audio.wav",
            #     500,
            #     "An unexpected error occurred.",
            # ),
        ],
    )
    def test_transcribe_audio_errors(
        self,
        file_path: str,
        expected_status_code: int,
        expected_detail: str,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:

        async def mock_transcribe_audio(file_path: str) -> None:
            if expected_status_code == 500:
                raise ValueError("Test ValueError")

        monkeypatch.setattr(
            "speech_api.app.routers.transcribe_audio",
            mock_transcribe_audio,
        )
        response = client.post("/transcribe", json={"file_path": file_path})
        assert response.status_code == expected_status_code
        assert response.json()["error"] == expected_detail