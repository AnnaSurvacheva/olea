"""Tests for Argon2id hashing."""

from auth.infrastructure.password_hasher import Argon2PasswordHasher

PASSWORD = "correct-horse"


def _hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher(
        time_cost=1,
        memory_cost=8 * 1024,
        parallelism=1,
    )


def test_hash_uses_argon2id() -> None:
    hashed = _hasher().hash(PASSWORD)

    assert hashed.startswith("$argon2id$")
    assert PASSWORD not in hashed


def test_verify_accepts_correct_password() -> None:
    hasher = _hasher()
    hashed = hasher.hash(PASSWORD)

    assert hasher.verify(PASSWORD, hashed) is True


def test_verify_rejects_wrong_password() -> None:
    hasher = _hasher()
    hashed = hasher.hash(PASSWORD)

    assert hasher.verify("wrong-password", hashed) is False


def test_verify_rejects_malformed_hash() -> None:
    assert _hasher().verify(PASSWORD, "not-an-argon2-hash") is False


def test_needs_rehash_is_false_for_current_parameters() -> None:
    hasher = _hasher()
    hashed = hasher.hash(PASSWORD)

    assert hasher.needs_rehash(hashed) is False


def test_needs_rehash_is_true_when_parameters_change() -> None:
    old_hasher = Argon2PasswordHasher(
        time_cost=1,
        memory_cost=8 * 1024,
        parallelism=1,
    )
    hashed = old_hasher.hash(PASSWORD)
    new_hasher = Argon2PasswordHasher(
        time_cost=2,
        memory_cost=8 * 1024,
        parallelism=1,
    )

    assert new_hasher.needs_rehash(hashed) is True


async def test_hash_in_thread_returns_argon2id() -> None:
    hashed = await _hasher().hash_in_thread(PASSWORD)

    assert hashed.startswith("$argon2id$")
    assert await _hasher().verify_in_thread(PASSWORD, hashed) is True
    assert await _hasher().verify_in_thread("wrong-password", hashed) is False
