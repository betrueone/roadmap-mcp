import shutil
from pathlib import Path

import pytest

from roadmap_mcp.catalog import Catalog
from roadmap_mcp.service import RoadmapService

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def all_categories(roadmap):
    return [*roadmap.hard_skills, *roadmap.soft_skills]


def all_skills(roadmap):
    return [skill for category in all_categories(roadmap) for skill in category.skills]


@pytest.fixture(scope="session")
def catalog():
    return Catalog(DATA_DIR)


@pytest.fixture(scope="session")
def service(catalog):
    return RoadmapService(catalog)


@pytest.fixture
def editable_data(tmp_path):
    target = tmp_path / "data"
    shutil.copytree(DATA_DIR, target)
    return target
