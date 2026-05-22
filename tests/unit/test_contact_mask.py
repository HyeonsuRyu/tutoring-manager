import pytest

from core.contact_mask import mask_contact


@pytest.mark.unit
def test_mask_contact():
    assert mask_contact("01012345678").endswith("5678")
    assert mask_contact("01012345678").startswith("*")
