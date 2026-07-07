"""Testes de CRUD simples: Categorias, Projetos, Papéis e Configurações."""

import pytest

from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.role import RoleCreate, RoleUpdate
from app.schemas.user import SettingsUpdate
from app.services.category_service import CategoryService
from app.services.project_service import ProjectService
from app.services.role_service import RoleService
from app.services.settings_service import SettingsService

pytestmark = pytest.mark.asyncio


async def test_category_crud(db_session, test_user: User):
    service = CategoryService(db_session)
    category = await service.create(test_user.id, CategoryCreate(name="Financeiro"))
    assert category.name == "Financeiro"

    updated = await service.update(category, CategoryUpdate(name="Financeiro pessoal"))
    assert updated.name == "Financeiro pessoal"

    await service.delete(updated)
    assert await service.get(category.id, test_user.id) is None


async def test_project_crud(db_session, test_user: User):
    service = ProjectService(db_session)
    project = await service.create(test_user.id, ProjectCreate(name="Website"))
    updated = await service.update(project, ProjectUpdate(percent_complete=42))
    assert float(updated.percent_complete) == 42.0

    await service.delete(updated)
    assert await service.get(project.id, test_user.id) is None


async def test_role_crud(db_session, test_user: User):
    service = RoleService(db_session)
    role = await service.create(test_user.id, RoleCreate(name="Saúde"))
    assert role.name == "Saúde"

    updated = await service.update(role, RoleUpdate(color="#ff0000"))
    assert updated.color == "#ff0000"

    await service.delete(updated)
    assert await service.get(role.id, test_user.id) is None


async def test_settings_seeded_and_updatable(db_session, test_user: User):
    service = SettingsService(db_session)
    settings = await service.get(test_user.id)
    assert settings is not None
    assert settings.pomodoro_work_minutes == 25

    updated = await service.update(settings, SettingsUpdate(pomodoro_work_minutes=50, pomodoro_break_minutes=10))
    assert updated.pomodoro_work_minutes == 50
    assert updated.pomodoro_break_minutes == 10
