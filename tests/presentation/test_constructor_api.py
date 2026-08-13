def payload(name: str = "API invoice workflow") -> dict:
    return {
        "name": name,
        "tasks": [
            {
                "task_key": "validate",
                "name": "Validate",
                "task_type": "DOCUMENT_VALIDATION",
                "is_start": True,
                "max_attempts": 1,
            },
            {
                "task_key": "review",
                "name": "Review",
                "task_type": "HUMAN_APPROVAL",
                "is_start": False,
                "max_attempts": None,
            },
            {
                "task_key": "notify",
                "name": "Notify",
                "task_type": "CREATE_NOTIFICATION",
                "is_start": False,
                "max_attempts": 1,
            },
            {
                "task_key": "archive",
                "name": "Archive",
                "task_type": "ARCHIVE_DOCUMENT",
                "is_start": False,
                "max_attempts": 3,
            },
        ],
        "transitions": [
            {
                "from_task_key": "validate",
                "to_task_key": "review",
                "condition": "SUCCESS",
            },
            {
                "from_task_key": "validate",
                "to_task_key": "notify",
                "condition": "FAILURE",
            },
            {
                "from_task_key": "review",
                "to_task_key": "archive",
                "condition": "SUCCESS",
            },
            {
                "from_task_key": "review",
                "to_task_key": "notify",
                "condition": "FAILURE",
            },
            {
                "from_task_key": "archive",
                "to_task_key": "notify",
                "condition": "ALWAYS",
            },
        ],
    }


def test_constructor_crud_validation_activation_and_revision_history(client) -> None:
    drafts = client.get("/api/v3/workflows/drafts")
    assert drafts.status_code == 200
    assert any(item["validation"]["valid"] for item in drafts.json())

    invalid = payload("Incomplete")
    for task in invalid["tasks"]:
        task["is_start"] = False
    report = client.post("/api/v3/workflows/validate", json=invalid)
    assert report.status_code == 200
    assert report.json()["valid"] is False
    assert any(item["rule"] == "FR-002" for item in report.json()["issues"])

    created_response = client.post(
        "/api/v3/workflows/drafts",
        json=payload(),
    )
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["validation"] == {"valid": True, "issues": []}

    first_response = client.post(
        f"/api/v3/workflows/drafts/{created['id']}/activate"
    )
    assert first_response.status_code == 200
    first = first_response.json()
    assert first["revision_number"] == 1

    revised_payload = payload("API invoice workflow v2")
    revised_payload["tasks"][0]["name"] = "Validate PDF and metadata"
    updated = client.put(
        f"/api/v3/workflows/drafts/{created['id']}",
        json=revised_payload,
    )
    assert updated.status_code == 200
    second = client.post(
        f"/api/v3/workflows/drafts/{created['id']}/activate"
    ).json()
    assert second["revision_number"] == 2

    original = client.get(
        f"/api/v3/workflows/revisions/{first['id']}"
    ).json()
    assert original["spec"]["tasks"][0]["name"] == "Validate"
    assert second["spec"]["tasks"][0]["name"] == "Validate PDF and metadata"

    deletion = client.delete(f"/api/v3/workflows/drafts/{created['id']}")
    assert deletion.status_code == 409


def test_constructor_rejects_scripts_plugins_and_unknown_task_types(client) -> None:
    executable = payload("Executable content")
    executable["tasks"][0]["script"] = "print('not allowed')"
    rejected_extra = client.post(
        "/api/v3/workflows/drafts",
        json=executable,
    )
    assert rejected_extra.status_code == 422

    unsupported = payload("Unsupported task")
    unsupported["tasks"][0]["task_type"] = "PYTHON_SCRIPT"
    rejected_type = client.post(
        "/api/v3/workflows/drafts",
        json=unsupported,
    )
    assert rejected_type.status_code == 422
    assert rejected_type.json()["detail"][0]["rule"] == "FR-049"
