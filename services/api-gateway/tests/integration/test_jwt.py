"""Integration tests for JWT validation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest


@pytest.mark.integration
class TestJWTValidation:
    """Test JWT validation middleware."""

    @pytest.fixture
    def valid_jwt_token(self, login_tokens):
        """Use a real access token issued by User Service."""
        return login_tokens["access_token"]

    @pytest.fixture
    def expired_jwt_token(self):
        """Generate an expired JWT token for testing."""
        from src.config import settings

        payload = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "role": "customer",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(minutes=30),  # Expired
            "iat": datetime.now(UTC) - timedelta(hours=1),
            "jti": "expired-jti",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token

    @pytest.fixture
    def invalid_signature_token(self):
        """Generate a token with invalid signature."""
        payload = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "role": "customer",
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=30),
            "iat": datetime.now(UTC),
            "jti": "invalid-sig-jti",
        }
        # Use wrong secret key
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
        return token

    def test_protected_endpoint_without_token(self, gateway_client):
        """Test accessing protected endpoint without token."""
        response = gateway_client.get("/api/v1/users/me")

        assert response.status_code in {401, 403}
        data = response.json()
        assert "detail" in data

    def test_protected_endpoint_with_valid_token(
        self,
        gateway_client_with_user_service,
        user_credentials,
        valid_jwt_token,
    ):
        """Test accessing protected endpoint with valid token."""
        response = gateway_client_with_user_service.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_credentials["email"]

    def test_protected_endpoint_with_expired_token(self, gateway_client, expired_jwt_token):
        """Test accessing protected endpoint with expired token."""
        response = gateway_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {expired_jwt_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        message = data["detail"]["error"]["message"].lower()
        assert "expired" in message or "invalid" in message

    def test_protected_endpoint_with_invalid_signature(
        self,
        gateway_client,
        invalid_signature_token,
    ):
        """Test accessing protected endpoint with token with invalid signature."""
        response = gateway_client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {invalid_signature_token}"},
        )

        assert response.status_code == 401
        data = response.json()
        message = data["detail"]["error"]["message"].lower()
        assert "invalid" in message or "signature" in message

    def test_protected_endpoint_with_malformed_token(self, gateway_client):
        """Test accessing protected endpoint with malformed token."""
        response = gateway_client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not-a-valid-jwt-token"}
        )

        assert response.status_code == 401
        data = response.json()
        message = data["detail"]["error"]["message"].lower()
        assert "invalid" in message

    def test_protected_endpoint_with_missing_bearer_prefix(
        self,
        gateway_client,
        valid_jwt_token,
    ):
        """Test accessing protected endpoint without Bearer prefix."""
        response = gateway_client.get(
            "/api/v1/users/me", headers={"Authorization": valid_jwt_token}
        )

        assert response.status_code in {401, 403}
        data = response.json()
        assert "detail" in data

    def test_jwt_payload_extraction(self, gateway_client_with_user_service, valid_jwt_token):
        """Test that JWT payload is correctly extracted and available."""
        response = gateway_client_with_user_service.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {valid_jwt_token}"}
        )

        assert response.status_code == 200

    def test_jwt_with_missing_required_claims(self, gateway_client):
        """Test JWT token with missing required claims (sub, email)."""
        from src.config import settings

        # Token missing 'sub' claim
        payload = {
            "email": "test@example.com",
            "role": "customer",
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=30),
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        response = gateway_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401
        data = response.json()
        message = data["detail"]["error"]["message"].lower()
        assert "invalid" in message or "claim" in message

    def test_public_endpoints_dont_require_jwt(self, gateway_client_with_user_service):
        """Test that public endpoints (login, register) don't require JWT."""
        email = f"public-{uuid4()}@example.com"
        password = "SecurePass123!"

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "New User"},
        )
        assert response.status_code == 201

        response = gateway_client_with_user_service.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
