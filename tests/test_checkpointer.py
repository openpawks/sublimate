import pytest

from langgraph.checkpoint.conformance import checkpointer_test, validate

from src.services.checkpointer import MyCheckpointer


@checkpointer_test(name="MyCheckpointer")
async def my_checkpointer():
    async with MyCheckpointer() as saver:
        yield saver


@pytest.mark.asyncio
async def test_conformance():
    report = await validate(my_checkpointer)
    report.print_report()
    assert report.passed_all_base()
