import asyncio

import pytest
from mcp import Client
from mcp.types import CallToolResult, CreateMessageResult, ElicitResult, TextContent

from mcp_starter.server import mcp


def text(result: CallToolResult) -> str:
    assert not result.is_error
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_sampling_and_elicitation(mode):
    async def sample(context, params):
        assert params.messages[0].content.text == "test prompt"
        assert params.max_tokens == 42
        return CreateMessageResult(
            role="assistant", content=TextContent(text="test response"), model="test"
        )

    async def elicit(context, params):
        if params.mode == "form":
            assert params.message == "Please confirm: deploy"
            return ElicitResult(action="accept", content={"confirm": True, "reason": "ready"})
        assert params.mode == "url"
        assert "github.com/SamMorrowDrums/mcp-starters" in params.url
        return ElicitResult(action="accept")

    async def run():
        async with Client(
            mcp, mode=mode, sampling_callback=sample, elicitation_callback=elicit
        ) as client:
            sampling = await client.call_tool("ask_llm", {"prompt": "test prompt", "maxTokens": 42})
            assert text(sampling) == "LLM Response: test response"
            confirmation = await client.call_tool("confirm_action", {"action": "deploy"})
            assert text(confirmation) == "Action confirmed: deploy\nReason: ready"
            feedback = await client.call_tool("get_feedback", {"question": "hello"})
            assert "Thank you for providing feedback!" in text(feedback)

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["legacy", "auto"])
@pytest.mark.parametrize("action", ["decline", "cancel"])
def test_elicitation_refusal(mode, action):
    async def elicit(context, params):
        return ElicitResult(action=action)

    async def run():
        async with Client(mcp, mode=mode, elicitation_callback=elicit) as client:
            confirmation = await client.call_tool("confirm_action", {"action": "deploy"})
            assert action in text(confirmation).lower()
            feedback = await client.call_tool("get_feedback", {"question": "hello"})
            assert ("No problem!" if action == "decline" else "cancelled") in text(feedback)

    asyncio.run(run())


def test_modern_input_response_requires_request_state():
    async def run():
        async with Client(mcp, mode="auto") as client:
            result = await client.call_tool(
                "confirm_action",
                {"action": "deploy"},
                input_responses={
                    "confirmation": ElicitResult(action="accept", content={"confirm": True})
                },
            )
            assert "Missing or invalid confirmation request state" in text(result)

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_invalid_confirmation_is_not_accepted(mode):
    async def elicit(context, params):
        return ElicitResult(action="accept", content={"confirm": "yes"})

    async def run():
        async with Client(mcp, mode=mode, elicitation_callback=elicit) as client:
            result = await client.call_tool("confirm_action", {"action": "deploy"})
            assert "Invalid confirmation response" in text(result)

    asyncio.run(run())
