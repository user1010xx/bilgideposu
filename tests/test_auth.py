from types import SimpleNamespace

import pytest

from bot.utils import auth as auth_mod


class FakeUser:
    def __init__(self, user_id, username=None):
        self.id = user_id
        self.username = username


class FakeUpdate:
    def __init__(self, user):
        self.effective_user = user


@pytest.fixture
def admin_config(monkeypatch):
    monkeypatch.setattr(auth_mod, "ADMIN_IDS", {111})
    monkeypatch.setattr(auth_mod, "ADMIN_USERNAMES", {"yetkili_user"})


def test_admin_by_id(admin_config):
    update = FakeUpdate(FakeUser(111))
    assert auth_mod.is_admin(update) is True


def test_admin_by_username(admin_config):
    update = FakeUpdate(FakeUser(999, "Yetkili_User"))
    assert auth_mod.is_admin(update) is True


def test_not_admin(admin_config):
    update = FakeUpdate(FakeUser(999, "normal_user"))
    assert auth_mod.is_admin(update) is False


def test_no_username_not_in_list(admin_config):
    update = FakeUpdate(FakeUser(999, None))
    assert auth_mod.is_admin(update) is False
