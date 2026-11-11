"""Verify SDK v2 subscriptions; the starter's resources themselves are static.

Modern clients receive resource events through subscriptions/listen. Legacy
clients are not offered resource subscriptions by this server.
"""

import asyncio

from mcp import Client
from mcp.shared.subscriptions import ResourcesListChanged, ResourceUpdated, ToolsListChanged

from mcp_starter.server import mcp


def test_modern_subscription_delivery():
    async def run():
        async with Client(mcp, mode="auto") as client:
            capabilities = client.session.server_capabilities
            assert capabilities is not None and capabilities.resources is not None
            assert capabilities.resources.subscribe and capabilities.resources.list_changed

            async with client.listen(
                resource_subscriptions=["about://server"],
                resources_list_changed=True,
                tools_list_changed=True,
            ) as subscription:
                assert subscription.honored.resource_subscriptions == ["about://server"]
                assert subscription.honored.resources_list_changed
                assert subscription.honored.tools_list_changed

                await mcp._subscriptions.publish(ResourceUpdated(uri="about://server"))
                await mcp._subscriptions.publish(ResourcesListChanged())
                result = await client.call_tool("load_bonus_tool", {})
                assert not result.is_error

                first = await asyncio.wait_for(anext(subscription), timeout=3)
                second = await asyncio.wait_for(anext(subscription), timeout=3)
                third = await asyncio.wait_for(anext(subscription), timeout=3)
                assert isinstance(first, ResourceUpdated) and first.uri == "about://server"
                assert isinstance(second, ResourcesListChanged)
                assert isinstance(third, ToolsListChanged)

    asyncio.run(run())


def test_legacy_resource_capabilities():
    async def run():
        async with Client(mcp, mode="legacy") as client:
            capabilities = client.session.server_capabilities
            assert capabilities is not None and capabilities.resources is not None
            assert not capabilities.resources.subscribe
            assert not capabilities.resources.list_changed

    asyncio.run(run())
