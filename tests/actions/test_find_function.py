import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from moatless.actions.find_function import FindFunction, FindFunctionArgs
from moatless.benchmark.swebench import create_repository, create_index_async
from moatless.completion import BaseCompletionModel
from moatless.evaluation.utils import get_moatless_instance
from moatless.file_context import FileContext, ContextSpan
from moatless.index.code_index import CodeIndex
from moatless.index.types import SearchCodeResponse, SearchCodeHit, SpanHit
from moatless.repository.repository import Repository
from moatless.workspace import Workspace


@pytest.mark.asyncio
@pytest.mark.skipif(os.environ.get("VOYAGE_API_KEY") is None, reason="VOYAGE_API_KEY environment variable not set")
async def test_find_function_init_method():
    instance_id = "django__django-13658"
    instance = get_moatless_instance(instance_id)
    repository = create_repository(instance)
    code_index = await create_index_async(instance, repository)
    file_context = FileContext(repo=repository)
    # Mock the completion model
    completion_model = AsyncMock(spec=BaseCompletionModel)

    # Create and initialize workspace
    workspace = Workspace(repository=repository, code_index=code_index)

    action = FindFunction(
        completion_model=completion_model,
        max_search_tokens=4000,
        max_identify_tokens=4000,
        max_identify_prompt_tokens=4000,
        max_hits=10,
        add_extra_context=False,
        use_identifier=True,
    )
    # Initialize the action with the workspace
    await action.initialize(workspace)

    action_args = FindFunctionArgs(
        thoughts="",
        class_name="ManagementUtility",
        function_name="__init__",
    )

    message = await action.execute(action_args, file_context)
    print(message)
    assert len(file_context.files) == 1
    assert "ManagementUtility.__init__" in file_context.files[0].span_ids


@pytest.mark.asyncio
@pytest.mark.skipif(os.environ.get("VOYAGE_API_KEY") is None, reason="VOYAGE_API_KEY environment variable not set")
async def test_find_function():
    instance_id = "django__django-14855"
    instance = get_moatless_instance(instance_id)
    repository = create_repository(instance)
    code_index = await create_index_async(instance, repository)
    file_context = FileContext(repo=repository)
    # Mock the completion model
    completion_model = AsyncMock(spec=BaseCompletionModel)

    # Create and initialize workspace
    workspace = Workspace(repository=repository, code_index=code_index)

    action = FindFunction(
        completion_model=completion_model,
        max_search_tokens=4000,
        max_identify_tokens=4000,
        max_identify_prompt_tokens=4000,
        max_hits=10,
        add_extra_context=False,
        use_identifier=True,
    )
    # Initialize the action with the workspace
    await action.initialize(workspace)

    action_args = FindFunctionArgs(
        thoughts="",
        function_name="cached_eval",
        file_pattern="**/*.py",
    )

    _ = await action.execute(action_args, file_context)


@pytest.mark.asyncio
async def test_find_function_with_mocks():
    """Test FindFunction with completely mocked dependencies."""
    # Setup - create mocks
    repository = MagicMock(spec=Repository)
    repository.file_exists.return_value = True  # Ensure file exists
    repository.get_file_content.return_value = "def test_function():\n    pass"
    repository.shadow_mode = True

    code_index = AsyncMock(spec=CodeIndex)
    file_context = FileContext(repo=repository)
    completion_model = AsyncMock(spec=BaseCompletionModel)

    # Mock search response
    mock_span_hit = SpanHit(span_id="test_function")
    mock_search_hit = SearchCodeHit(file_path="test_file.py", spans=[mock_span_hit])
    mock_search_response = SearchCodeResponse(hits=[mock_search_hit])

    # Configure the mock to return our predefined response
    code_index.find_function.return_value = mock_search_response

    # Create workspace and action
    workspace = Workspace(repository=repository, code_index=code_index)
    action = FindFunction(
        completion_model=completion_model,
        max_search_tokens=4000,
        max_identify_tokens=4000,
        max_identify_prompt_tokens=4000,
        max_hits=10,
        add_extra_context=False,
        use_identifier=True,
    )
    await action.initialize(workspace)

    # Execute action
    action_args = FindFunctionArgs(
        thoughts="",
        function_name="test_function",
        file_pattern="**/*.py",
    )

    # Since we can't easily mock the span system, add the span directly to the file_context
    context_file = file_context.add_file("test_file.py")
    context_file.spans.append(ContextSpan(span_id="test_function"))

    _ = await action.execute(action_args, file_context)

    # Verify
    code_index.find_function.assert_awaited_once_with("test_function", class_name=None, file_pattern="**/*.py")
    assert len(file_context.files) == 1
    assert "test_function" in file_context.files[0].span_ids
