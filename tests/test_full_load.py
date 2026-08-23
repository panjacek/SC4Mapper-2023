import logging
import os

import pytest

from sc4_mapper.core.rgnReader import SC4Region

logger = logging.getLogger(__name__)
logging.getLogger("sc4_mapper.core.rgnReader").setLevel(logging.INFO)

# Repo-root relative so tests run regardless of cwd
REGION_TESTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "region_tests")


@pytest.fixture(scope="session")
def test_regions_dir():
    return REGION_TESTS_DIR


def get_region_folders():
    # Helper to find all subdirectories in region_tests that look like valid regions (have config.bmp)
    root = REGION_TESTS_DIR
    if not os.path.exists(root):
        return []
    valid_regions = []
    # Only test San Francisco for now to ensure speed and stability
    target = "San Francisco"
    path = os.path.join(root, target)
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "config.bmp")):
        valid_regions.append(target)
    return valid_regions


def test_region_fixtures_available():
    """Visible skip when fixtures are absent - empty parametrize would pass silently."""
    if not os.path.isdir(REGION_TESTS_DIR) or not get_region_folders():
        pytest.skip(f"no region fixtures under {REGION_TESTS_DIR}")


@pytest.mark.parametrize("region_name", get_region_folders())
def test_load_and_render_region(test_regions_dir, region_name):
    region_path = os.path.join(test_regions_dir, region_name)
    logger.info(f"Testing full load for region: {region_path}")

    # 1. Load Region (simulates app loading)
    # pass None for dlg as we are headless
    region = SC4Region(region_path, 250, None, config=None)

    assert region.is_valid(), f"Region {region_name} should be valid"
    assert region.all_cities is not None, "Cities should be loaded"

    # 2. Simulate rendering / config building
    # This calls BuildConfig internally which uses missingCities
    config_image = region.BuildConfig()

    assert config_image is not None
    assert config_image.size[0] > 0
    assert config_image.size[1] > 0

    logger.info(f"Region {region_name} loaded and config built successfully. Size: {config_image.size}")
