"""Example of how to load documents into VectorDB before allowing analitiq access them."""

import os
import pathlib
import tempfile
from unittest.mock import patch
import pytest
import asyncio

from analitiq.vectordb.weaviate import WeaviateHandler
from analitiq.base.llm.BaseLlm import BaseLlm
from analitiq.agents.search_vdb.search_vdb import SearchVdb

@pytest.fixture(name="temp_files")
def temp_files_fixture():
    """Erstellt temporäre Textdateien."""
    files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_file:
            temp_file.write(f'This is the content of file {i+1}. Can you please correct this stuff so we get doc length\n'.encode('utf-8'))
            files.append(temp_file.name)
    yield files
    # Löschen der Dateien nach dem Test
    for file in files:
        os.remove(file)


@pytest.fixture(name="mock_client", autouse=True)
def mock_client_fixture():
    """Mock the client."""
    with patch("weaviate.connect_to_wcs") as mock_connect:
        mock_client = mock_connect.return_value
        yield mock_client


@pytest.fixture(name="params", autouse=True)
def params_fixture():
    """Mock some parameters."""
    return {
        "host": "https://test-analitiq-5mwe1rof.weaviate.network",
        "api_key": "Wy1q2YlOFAMETXA7OeUBAvNS4iUx3qnIpy24",
        "collection_name": "analitiq123123",
    }


@pytest.fixture(name="handler")
def handler_fixture(params):
    """Use the Weaviatehandler with mocked params."""
    wv = WeaviateHandler(params)
    # we should mock a collection which can be used for searching. the weaviate db using bm25.
    # maybe replaece remote db with embedded local db for better testing?
    return wv

def test_docs_agent(handler, mock_client):
    """Test the complete document retrieval Agent."""
    mock_client.collections.exists.return_value = False
    handler.connect()

    user_prompt = "Please give me revenues by month."

    llm_params = {"type": "bedrock"
    , "name": "aws_llm"
    , "api_key": None
    , "temperature": 0.0
    , "llm_model_name": "Dummy"
    , "credentials_profile_name": "CREDENTIALS_PROFILE_NAME"
    , "provider": "anthropic"
    , "aws_access_key_id": "AWS_ACCESS_KEY_ID"
    , "aws_secret_access_key": "AWS_SECRET_ACCESS_KEY"
    , "region_name": "eu-central-1"}
    llm = BaseLlm(llm_params)

    agent = SearchVdb(llm, vdb=handler, search_mode="hybrid")
    result_generator = agent.arun(user_prompt)

    async def process_results():
        async for result in result_generator:
            if isinstance(result, str):
                print(result)
                pass  # Print incremental results
            else:
                print(result)
                pass  # Capture the final BaseResponse object

    # Run the async function
    asyncio.run(process_results())

    assert 1==2
