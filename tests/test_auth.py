def _get_csrf(client, url="/auth/register"):
    response = client.get(url)
    assert response.status_code == 200
    return client.cookies.get("csrf_token")


def test_register_creates_session_and_redirects(client):
    csrf = _get_csrf(client)
    response = client.post(
        "/auth/register",
        data={
            "email": "newuser@example.com",
            "password": "correct-horse-battery",
            "confirm_password": "correct-horse-battery",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert client.cookies.get("eh_session") is not None


def test_register_rejects_mismatched_csrf(client):
    _get_csrf(client)
    response = client.post(
        "/auth/register",
        data={
            "email": "another@example.com",
            "password": "correct-horse-battery",
            "confirm_password": "correct-horse-battery",
            "csrf_token": "not-the-real-token",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "flash" in response.headers["location"]
    assert client.cookies.get("eh_session") is None


def test_register_rejects_weak_password(client):
    csrf = _get_csrf(client)
    response = client.post(
        "/auth/register",
        data={"email": "weak@example.com", "password": "short", "confirm_password": "short", "csrf_token": csrf},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert client.cookies.get("eh_session") is None


def test_login_with_wrong_password_fails(client):
    csrf = _get_csrf(client)
    client.post(
        "/auth/register",
        data={
            "email": "loginuser@example.com",
            "password": "correct-horse-battery",
            "confirm_password": "correct-horse-battery",
            "csrf_token": csrf,
        },
        follow_redirects=False,
    )
    client.cookies.delete("eh_session")

    csrf2 = _get_csrf(client, "/auth/login")
    response = client.post(
        "/auth/login",
        data={"email": "loginuser@example.com", "password": "wrong-password", "csrf_token": csrf2},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert client.cookies.get("eh_session") is None


def test_unauthenticated_landing_redirects_to_login(client):
    client.cookies.clear()
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"
