# pylint: disable=redefined-outer-name

import pytest
import os
from dotenv import load_dotenv
from analitiq.factories.vector_database_factory import VectorDatabaseFactory
from weaviate.collections.classes.internal import QueryReturn

COLLECTION_NAME = "test_collection"


@pytest.fixture(autouse=True, scope="module")
def params():
    return {
        "collection_name": COLLECTION_NAME,
        "tenant_name": COLLECTION_NAME,
        "type": "weaviate",
        "host": os.getenv("WEAVIATE_URL"),
        "api_key": os.getenv("WEAVIATE_CLIENT_SECRET"),
    }


@pytest.fixture(autouse=True, scope="module")
def load_environment():
    """Loads environment variables from .env file"""

    load_dotenv(".env", override=True)


@pytest.fixture(scope="module")
def weaviate_handler(params):
    handler = VectorDatabaseFactory.create_database(params)
    yield handler


test_documents = [
    {
        "document_name": "test_document_1.txt",
        "content": "This is the first test document.",
    },
    {
        "document_name": "test_document_2.txt",
        "content": "Another document for testing.",
    },
    {
        "document_name": "project_plan.txt",
        "content": "This document contains the project plan.",
    },
    {"document_name": "summary_report.txt", "content": "The summary of all reports."},
    {
        "document_name": "test_document_3.txt",
        "content": "This document is for additional tests.",
    },
]


def create_documents(documents, test_dir: str = "test_dir"):
    os.makedirs(test_dir, exist_ok=True)

    for doc in documents:
        with open(os.path.join(test_dir, doc["document_name"]), "w") as f:
            f.write(doc["content"])

    print("Documents created successfully.")


def delete_documents(documents, test_dir: str = "test_dir"):
    for doc in documents:
        try:
            os.remove(os.path.join(test_dir, doc["document_name"]))
            print(f"Deleted {doc['document_name']} successfully.")
        except FileNotFoundError:
            print(f"{doc['document_name']} does not exist.")

    os.rmdir(test_dir)


def test_create_collection(weaviate_handler):
    with weaviate_handler:
        check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
        if check:
            weaviate_handler.delete_collection(COLLECTION_NAME)

        collection_name = weaviate_handler.create_collection(COLLECTION_NAME)
        assert collection_name == COLLECTION_NAME

        check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
        assert check == True


def test_load_single_document(weaviate_handler):
    test_document_path = "document.txt"
    with open(test_document_path, "w") as f:
        f.write("This is a test document.")

    with weaviate_handler:
        response = weaviate_handler.load_file(test_document_path)

    assert response > 0

    os.remove(test_document_path)


def test_load_documents_from_directory(weaviate_handler):
    test_dir = "test_dir"
    create_documents(test_documents, test_dir)

    with weaviate_handler:
        response = weaviate_handler.load_dir(test_dir, "txt")

    assert response >= 3

    delete_documents(test_documents, test_dir)


def test_keyword_search(weaviate_handler):
    query = "test document"
    with weaviate_handler:
        result = weaviate_handler.kw_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_vector_search(weaviate_handler):
    query = "test document"
    with weaviate_handler:
        result = weaviate_handler.vector_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_hybrid_search(weaviate_handler):
    query = "test document"
    with weaviate_handler:
        result = weaviate_handler.hybrid_search(query)

    assert isinstance(result, QueryReturn)
    assert len(result.objects) == 3


def test_filter_count__equal(weaviate_handler):
    filter_expression = {
        "or": [
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "like",
                        "value": "test_document",
                    },
                    {"property": "document_name", "operator": "like", "value": "1"},
                ]
            },
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_1.txt",
                    },
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_2.txt",
                    },
                ]
            },
        ]
    }
    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression=filter_expression)

    assert result.total_count == 1


def test_filter_count_and(weaviate_handler):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "like", "value": "test_document"},
            {"property": "content", "operator": "like", "value": "first"},
        ]
    }
    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression)

    assert result.total_count == 1


def test_filter_count__or(weaviate_handler):
    filter_expression = {
        "or": [
            {"property": "document_name", "operator": "like", "value": "summary"},
            {"property": "content", "operator": "like", "value": "project"},
        ]
    }

    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression)

    assert result.total_count == 2


def test_filter_count__simple_and_complex_filter(weaviate_handler):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "like", "value": "test_document"},
            {
                "or": [
                    {"property": "content", "operator": "like", "value": "tests"},
                    {"property": "content", "operator": "like", "value": "testing"},
                ]
            },
        ]
    }

    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression)

    assert result.total_count == 2


def test_filter_count__complex_filter(weaviate_handler):
    filter_expression = {
        "and": [
            {
                "or": [
                    {"property": "document_name", "operator": "like", "value": "test"},
                    {
                        "property": "content",
                        "operator": "!=",
                        "value": "This is the first test document.",
                    },
                ]
            },
            {
                "or": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "project_plan.txt",
                    },
                    {"property": "content", "operator": "like", "value": "project"},
                ]
            },
        ]
    }

    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression)

    assert result.total_count == 1


def test_filter_group_count(weaviate_handler):
    filter_expression = {
        "property": "document_name",
        "operator": "like",
        "value": "test",
    }

    with weaviate_handler:
        result = weaviate_handler.filter_group_count(filter_expression, "document_name")

    # Assert that there are exactly 3 AggregateGroup objects
    assert len(result.groups) == 3

    # Assert that each AggregateGroup object has total_count = 1
    for group in result.groups:
        assert group.total_count == 1


def test_search_filter(weaviate_handler):
    query = "document"
    filter_expression = {
        "and": [
            {
                "or": [
                    {"property": "document_name", "operator": "like", "value": "test"},
                    {
                        "property": "content",
                        "operator": "!=",
                        "value": "This is the first test document.",
                    },
                ]
            }
        ]
    }

    with weaviate_handler:
        result = weaviate_handler.search_filter(query, filter_expression)

    assert len(result.objects) == 4


def test_filter_count__like(weaviate_handler):
    filter_expression = {
        "or": [
            {
                "and": [
                    {"property": "document_name", "operator": "like", "value": "test"},
                    {"property": "source", "operator": "like", "value": "test"},
                ]
            },
            {
                "and": [
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_1.txt",
                    },
                    {
                        "property": "document_name",
                        "operator": "=",
                        "value": "test_document_1",
                    },
                ]
            },
        ]
    }
    with weaviate_handler:
        result = weaviate_handler.filter_count(filter_expression)

    assert result.total_count == 3


def test_filter(weaviate_handler):
    filter_expression = {
        "and": [
            {"property": "document_name", "operator": "=", "value": "project_plan.txt"},
        ]
    }

    with weaviate_handler:
        result = weaviate_handler.filter(filter_expression)
        print(QueryReturn)
    assert len(result.objects) == 1


def test_filter_delete(weaviate_handler):

    with weaviate_handler:
        result = weaviate_handler.filter_delete('document_name', 'test_document_1.txt')

    assert result.matches == 1
    assert result.successful == 1


def test_delete_collection(weaviate_handler):

    with weaviate_handler:
        result = weaviate_handler.delete_collection(COLLECTION_NAME)
    assert result == True

    with weaviate_handler:
        check = weaviate_handler.client.collections.exists(COLLECTION_NAME)
    assert check == False

