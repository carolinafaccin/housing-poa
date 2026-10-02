"""The pipeline must reproduce the counts published in the paper (needs the dataset; skipped without config)."""
import pytest

from housing import config, data, metrics

CFG = config.ROOT / "config" / "config.local.json"
pytestmark = pytest.mark.skipif(not CFG.exists(), reason="config/config.local.json not set")


@pytest.fixture(scope="module")
def condos():
    dataset_dir, _, _ = config.load()
    data.fetch_dataset(dataset_dir)
    return data.load_condominiums(dataset_dir)


def test_published_counts(condos):
    val = metrics.validate(condos)
    assert val["ok"].all(), val[~val["ok"]].to_string()


def test_income_classes_close_to_paper(condos):
    inc = metrics.income_comparison(condos)
    assert (inc["published_pct"] - inc["computed_pct"]).abs().max() < 6
