"""Mock a complete weaviate db and it's important returns.

So we can test that the modules are working together as expected.
This is needed for simulating the example tests.
"""
import pytest
import weaviate

@pytest.Fixture(name="weaviate_connect_to_wcs")
def weaviate_connect_to_wcs():
    """Replace weaviate.connect_to_wcs by my mocked function which."""
    pass


@pytest.Fixture(name="weaviate_client")
def weaviate_client_fixture():
    """Return a mocked Weaviate Client needed for testing."""
    pass