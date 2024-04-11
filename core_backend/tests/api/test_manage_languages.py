import pytest
from fastapi.testclient import TestClient


class TestManageLanguage:
    def test_create_and_delete_language(
        self,
        client: TestClient,
        fullaccess_token: str,
    ) -> None:
        language_name = "test-language"
        response = client.post(
            "/language/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": language_name, "is_default": False},
        )
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["language_name"] == language_name.upper()
        response = client.delete(
            f"/language/{json_response['language_id']}/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )
        assert response.status_code == 200

    def test_edit_language(
        self,
        client: TestClient,
        existing_languages: tuple[dict, dict],
        fullaccess_token: str,
        readonly_token: str,
    ) -> None:
        new_language = "ZULU"

        response = client.put(
            f"/language/{existing_languages[0]['language_id']}/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": new_language, "is_default": True},
        )
        assert response.status_code == 200

        response = client.get(
            f"/language/{existing_languages[0]['language_id']}",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )

        assert response.status_code == 200
        assert response.json()["language_name"] == new_language

    @pytest.mark.parametrize(
        "language_name, expected_status",
        [
            ("test-language-new", 200),
            ("test_language", 422),
            ("TESTLANGUAGE", 200),
            ("#language", 422),
        ],
    )
    def test_language_name_validation(
        self,
        client: TestClient,
        fullaccess_token: str,
        language_name: str,
        expected_status: int,
    ) -> None:
        response = client.post(
            "/language/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": language_name, "is_default": False},
        )
        assert response.status_code == expected_status

    def test_language_name_unique(
        self,
        client: TestClient,
        existing_languages: tuple[dict, dict],
        fullaccess_token: str,
    ) -> None:
        language_name = "HINDI"
        response = client.post(
            "/language/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": language_name, "is_default": False},
        )
        assert response.status_code == 400

    def test_delete_default_language(
        self,
        existing_languages: tuple[dict, dict],
        client: TestClient,
        fullaccess_token: str,
        readonly_token: str,
    ) -> None:
        response = client.get(
            "/language/default",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert response.status_code == 200
        default_id = response.json()["language_id"]
        response = client.delete(
            f"/language/{default_id}/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "language_name",
        [
            ("FIRST-DEFAULT"),
            ("SECOND-DEFAULT"),
        ],
    )
    def test_always_one_default_language(
        self,
        client: TestClient,
        existing_languages: tuple,
        language_name: str,
        fullaccess_token: str,
        readonly_token: str,
    ) -> None:
        response = client.post(
            "/language/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": language_name, "is_default": True},
        )
        new_default_id = response.json()["language_id"]
        assert response.status_code == 200
        assert response.json()["is_default"] is True

        response = client.get(
            "/language/default",
            headers={"Authorization": f"Bearer {readonly_token}"},
        )
        assert response.status_code == 200
        assert response.json()["language_id"] == new_default_id

        response = client.put(
            f"/language/{existing_languages[0]['language_id']}/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": "XHOSA", "is_default": True},
        )
        assert response.status_code == 200
        assert response.json()["is_default"] is True

    def test_default_language_cannot_be_unset(
        self,
        client: TestClient,
        existing_languages: tuple[dict, dict],
        fullaccess_token: str,
    ) -> None:
        response = client.put(
            f"/language/{existing_languages[0]['language_id']}/",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={"language_name": "XHOSA", "is_default": False},
        )
        assert response.status_code == 400