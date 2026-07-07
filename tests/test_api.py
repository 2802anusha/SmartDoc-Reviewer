def test_health(client):

    response = client.get("/")

    assert response.status_code == 200


def test_submit_review(client):

    payload = {
        "pr_url": "https://github.com/demo/repo/pull/1"
    }

    response = client.post(
        "/review",
        json=payload
    )

    assert response.status_code in (200, 201)