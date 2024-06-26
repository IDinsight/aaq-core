from io import BytesIO
from typing import Generator

import pandas as pd
import pytest
from fastapi.testclient import TestClient


def _dict_to_csv_bytes(data: dict) -> BytesIO:
    """
    Convert a dictionary to a CSV file in bytes
    """

    df = pd.DataFrame(data)
    csv_bytes = BytesIO()
    df.to_csv(csv_bytes, index=False)
    csv_bytes.seek(0)

    return csv_bytes


class TestImportContent:
    @pytest.fixture
    def data_valid(self) -> BytesIO:
        data = {
            "content_title": ["csv title 1", "csv title 2"],
            "content_text": ["csv text 1", "csv text 2"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_empty_csv(self) -> BytesIO:
        data: dict = {}
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_no_rows(self) -> BytesIO:
        data: dict = {
            "content_title": [],
            "content_text": [],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_title_spaces_only(self) -> BytesIO:
        data: dict = {
            "content_title": ["  "],
            "content_text": ["csv text 1"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_text_spaces_only(self) -> BytesIO:
        data: dict = {
            "content_title": ["csv title 1"],
            "content_text": ["  "],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_missing_columns(self) -> BytesIO:
        data = {
            "wrong_column_1": ["Value 1", "Value 2"],
            "wrong_column_2": ["Value 3", "Value 4"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_title_missing(self) -> BytesIO:
        data = {
            "content_title": ["", "csv text 1"],
            "content_text": ["csv title 2", "csv text 2"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_text_missing(self) -> BytesIO:
        data = {
            "content_title": ["csv title 1", "csv title 2"],
            "content_text": ["", "csv text 2"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_long_title(self) -> BytesIO:
        data = {
            "content_title": ["a" * 151],
            "content_text": ["Valid text"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_long_text(self) -> BytesIO:
        data = {
            "content_title": ["Valid title"],
            "content_text": ["a" * 2001],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_duplicate_titles(self) -> BytesIO:
        data = {
            "content_title": ["Duplicate title", "Duplicate title"],
            "content_text": ["Text 1", "Text 2"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_duplicate_texts(self) -> BytesIO:
        data = {
            "content_title": ["Title 1", "Title 2"],
            "content_text": ["Duplicate text", "Duplicate text"],
        }
        return _dict_to_csv_bytes(data)

    test_data = [
        ("data_empty_csv", "empty_data"),
        ("data_no_rows", "no_rows_csv"),
        ("data_title_spaces_only", "empty_title"),
        ("data_text_spaces_only", "empty_text"),
        ("data_missing_columns", "missing_columns"),
        ("data_title_missing", "empty_title"),
        ("data_text_missing", "empty_text"),
        ("data_long_title", "title_too_long"),
        ("data_long_text", "texts_too_long"),
        ("data_duplicate_titles", "duplicate_titles"),
        ("data_duplicate_texts", "duplicate_texts"),
    ]

    async def test_csv_import_success(
        self,
        client: TestClient,
        data_valid: BytesIO,
        fullaccess_token: str,
    ) -> None:
        response = client.post(
            "/content/csv-upload",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            files={"file": ("test.csv", data_valid, "text/csv")},
        )
        assert response.status_code == 200

        json_response = response.json()
        for content in json_response:
            content_id = content["content_id"]
            response = client.delete(
                f"/content/{content_id}",
                headers={"Authorization": f"Bearer {fullaccess_token}"},
            )
            assert response.status_code == 200

    @pytest.mark.parametrize("mock_csv_data, expected_error_type", test_data)
    async def test_csv_import_checks(
        self,
        client: TestClient,
        mock_csv_data: BytesIO,
        expected_error_type: str,
        request: pytest.FixtureRequest,
        fullaccess_token: str,
    ) -> None:
        # fetch data from the fixture
        mock_csv_file = request.getfixturevalue(mock_csv_data)

        response = client.post(
            "/content/csv-upload",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            files={"file": ("test.csv", mock_csv_file, "text/csv")},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["errors"][0]["type"] == expected_error_type


class TestDBDuplicates:
    @pytest.fixture(scope="function")
    def existing_content_in_db(
        self,
        client: TestClient,
        fullaccess_token: str,
    ) -> Generator[str, None, None]:
        response = client.post(
            "/content",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={
                "content_title": "Title in DB",
                "content_text": "Text in DB",
                "content_tags": [],
                "content_metadata": {},
            },
        )
        content_id = response.json()["content_id"]
        yield content_id
        client.delete(
            f"/content/{content_id}",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )

    @pytest.fixture
    def data_title_in_db(self) -> BytesIO:
        # Assuming "Title in DB" is a title that exists in the database
        data = {
            "content_title": ["Title in DB"],
            "content_text": ["New text"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.fixture
    def data_text_in_db(self) -> BytesIO:
        # Assuming "Text in DB" is a text that exists in the database
        data = {
            "content_title": ["New title"],
            "content_text": ["Text in DB"],
        }
        return _dict_to_csv_bytes(data)

    @pytest.mark.parametrize(
        "mock_csv_data, expected_error_type",
        [("data_title_in_db", "title_in_db"), ("data_text_in_db", "text_in_db")],
    )
    async def test_csv_import_db_duplicates(
        self,
        client: TestClient,
        fullaccess_token: str,
        mock_csv_data: BytesIO,
        expected_error_type: str,
        request: pytest.FixtureRequest,
        existing_content_in_db: str,
    ) -> None:
        """
        This test uses the existing_content_in_db fixture to create a content in the
        database and then tries to import a CSV file with a title or text that already
        exists in the database.
        """
        mock_csv_file = request.getfixturevalue(mock_csv_data)
        response_text_dupe = client.post(
            "/content/csv-upload",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            files={"file": ("test.csv", mock_csv_file, "text/csv")},
        )
        assert response_text_dupe.status_code == 400
        assert (
            response_text_dupe.json()["detail"]["errors"][0]["type"]
            == expected_error_type
        )
