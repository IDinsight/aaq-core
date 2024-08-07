from datetime import datetime, timezone
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient

from core_backend.app.urgency_rules.models import UrgencyRuleDB
from core_backend.app.urgency_rules.routers import _convert_record_to_schema

from .conftest import async_fake_embedding

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


@pytest.fixture(
    scope="function",
    params=[
        ("test ud rule 1 - no metadata", {}),
        ("test ud rule 2 - with metadata", {"meta_key": "meta_value"}),
    ],
)
def existing_rule_id(
    request: pytest.FixtureRequest, client: TestClient, fullaccess_token: str
) -> Generator[str, None, None]:
    response = client.post(
        "/urgency-rules",
        headers={"Authorization": f"Bearer {fullaccess_token}"},
        json={
            "urgency_rule_text": request.param[0],
            "urgency_rule_metadata": request.param[1],
        },
    )
    rule_id = response.json()["urgency_rule_id"]
    yield rule_id
    client.delete(
        f"/urgency-rules/{rule_id}",
        headers={"Authorization": f"Bearer {fullaccess_token}"},
    )


class TestManageUDRules:
    @pytest.mark.parametrize(
        "urgency_rule_text, urgency_rule_metadata",
        [
            ("test rule 3", {}),
            ("test rule 4", {"meta_key": "meta_value"}),
        ],
    )
    def test_create_and_delete_UDrules(
        self,
        client: TestClient,
        urgency_rule_text: str,
        fullaccess_token: str,
        urgency_rule_metadata: Dict[Any, Any],
    ) -> None:
        response = client.post(
            "/urgency-rules",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={
                "urgency_rule_text": urgency_rule_text,
                "urgency_rule_metadata": urgency_rule_metadata,
            },
        )
        assert response.status_code == 200
        json_response = response.json()
        assert json_response["urgency_rule_metadata"] == urgency_rule_metadata
        assert "urgency_rule_id" in json_response

        response = client.delete(
            f"/urgency-rules/{json_response['urgency_rule_id']}",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "urgency_rule_text, urgency_rule_metadata",
        [
            ("test rule 3 - edited", {}),
            (
                "test rule 4 - edited",
                {"new_meta_key": "new meta_value", "meta_key": "meta_value_edited #2"},
            ),
        ],
    )
    def test_edit_and_retrieve_UDrules(
        self,
        client: TestClient,
        existing_rule_id: int,
        urgency_rule_text: str,
        fullaccess_token: str,
        urgency_rule_metadata: Dict[Any, Any],
    ) -> None:
        response = client.put(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={
                "urgency_rule_text": urgency_rule_text,
                "urgency_rule_metadata": urgency_rule_metadata,
            },
        )

        assert response.status_code == 200

        response = client.get(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )
        assert response.status_code == 200
        assert response.json()["urgency_rule_text"] == urgency_rule_text
        edited_metadata = response.json()["urgency_rule_metadata"]

        assert all(edited_metadata[k] == v for k, v in urgency_rule_metadata.items())

    def test_edit_UDrules_not_found(
        self, client: TestClient, fullaccess_token: str
    ) -> None:
        response = client.put(
            "/urgency-rules/12345",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
            json={
                "urgency_rule_text": "sample text",
                "urgency_rule_metadata": {"key": "value"},
            },
        )

        assert response.status_code == 404

    def test_list_UDrules(
        self, client: TestClient, existing_rule_id: int, fullaccess_token: str
    ) -> None:
        response = client.get(
            "/urgency-rules/", headers={"Authorization": f"Bearer {fullaccess_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_delete_UDrules(
        self, client: TestClient, existing_rule_id: int, fullaccess_token: str
    ) -> None:
        response = client.delete(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token}"},
        )
        assert response.status_code == 200


class TestMultUserManageUDRules:
    def user2_get_user1_UDrule(
        self,
        client: TestClient,
        existing_rule_id: str,
        fullaccess_token_user2: str,
    ) -> None:
        response = client.get(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token_user2}"},
        )
        assert response.status_code == 404

    def user2_edit_user1_UDrule(
        self,
        client: TestClient,
        existing_rule_id: str,
        fullaccess_token_user2: str,
    ) -> None:
        response = client.put(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token_user2}"},
            json={
                "urgency_rule_text": "user2 rule",
                "urgency_rule_metadata": {},
            },
        )
        assert response.status_code == 404

    def user2_delete_user1_UDrule(
        self,
        client: TestClient,
        existing_rule_id: str,
        fullaccess_token_user2: str,
    ) -> None:
        response = client.delete(
            f"/urgency-rules/{existing_rule_id}",
            headers={"Authorization": f"Bearer {fullaccess_token_user2}"},
        )
        assert response.status_code == 404


async def test_convert_record_to_schema() -> None:
    _id = 1
    record = UrgencyRuleDB(
        urgency_rule_id=_id,
        user_id=123,
        urgency_rule_text="sample text",
        urgency_rule_vector=await async_fake_embedding(),
        urgency_rule_metadata={"extra_field": "extra value"},
        created_datetime_utc=datetime.now(timezone.utc),
        updated_datetime_utc=datetime.now(timezone.utc),
    )
    result = _convert_record_to_schema(record)
    assert result.urgency_rule_id == _id
    assert result.urgency_rule_text == "sample text"
    assert result.urgency_rule_metadata["extra_field"] == "extra value"
