from __future__ import annotations

from fala_gavea.infrastructure.repositories.anonymous_token_repository import (
    SQLAlchemyAnonymousTokenRepository,
)


def test_save_and_find_by_hash(db_session, sample_report_type, citizen_headers, client):
    """Create a report (anonymous), then verify token lookup."""
    # Create anonymous report via API to get a valid report_id
    resp = client.post(
        "/reports",
        json={
            "text": "Buraco na calcada perto do mercado",
            "lat": -22.971,
            "lon": -43.211,
            "urgency": "media",
            "report_type_id": sample_report_type,
            "anonymous": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    report_id = data["id"]
    claim_token = data["anonymous_claim_token"]
    assert claim_token is not None

    # Verify token lookup works in the repository directly
    from hashlib import sha256
    token_hash = sha256(claim_token.encode()).hexdigest()
    repo = SQLAlchemyAnonymousTokenRepository(db_session)
    found = repo.find_report_ids_by_hash(token_hash)
    assert report_id in found


def test_find_by_hash_unknown_returns_empty(db_session):
    repo = SQLAlchemyAnonymousTokenRepository(db_session)
    result = repo.find_report_ids_by_hash("nonexistenthash")
    assert result == []
