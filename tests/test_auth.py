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


class FakeChat:
    def __init__(self, chat_id, title, chat_type="supergroup"):
        self.id = chat_id
        self.title = title
        self.type = chat_type


class FakeGroupUpdate:
    def __init__(self, chat):
        self.effective_chat = chat


def test_allowed_group_by_name(monkeypatch):
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_IDS", None)
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_NAMES", {"bilgi"})
    chat = FakeChat(-1001, "BİLGİ")
    assert auth_mod.is_allowed_group(FakeGroupUpdate(chat)) is True


def test_rejected_group_by_name(monkeypatch):
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_IDS", None)
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_NAMES", {"bilgi"})
    chat = FakeChat(-1002, "Başka Grup")
    assert auth_mod.is_allowed_group(FakeGroupUpdate(chat)) is False


def test_all_groups_when_no_filter(monkeypatch):
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_IDS", None)
    monkeypatch.setattr(auth_mod, "ALLOWED_GROUP_NAMES", None)
    chat = FakeChat(-1003, "Herhangi")
    assert auth_mod.is_allowed_group(FakeGroupUpdate(chat)) is True
