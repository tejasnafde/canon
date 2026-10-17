import os

os.environ.setdefault("CANON_FAKE_LLM", "1")  # CANON_FAKE_LLM=0 CANON_RECORD=1 re-records fixtures
os.environ["CANON_MEMORY_STORE"] = "1"

import pytest  # noqa: E402

from canon import llm, store  # noqa: E402


@pytest.fixture(autouse=True)
def fresh():
    llm.FAKE_RESPONSES.clear()
    yield store.reset_store_for_tests()
    llm.FAKE_RESPONSES.clear()
