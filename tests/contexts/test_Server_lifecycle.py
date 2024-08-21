import asyncio
import logging
import platform
import random

import pytest

from supriya.contexts.realtime import (
    DEFAULT_HEALTHCHECK,
    AsyncServer,
    BootStatus,
    Server,
    ServerLifecycleEvent,
)
from supriya.exceptions import (
    OwnedServerShutdown,
    ServerCannotBoot,
    ServerOnline,
    TooManyClients,
    UnownedServerShutdown,
)
from supriya.osc import find_free_port
from supriya.scsynth import kill

supernova = pytest.param(
    "supernova",
    marks=pytest.mark.skipif(
        platform.system() == "Windows", reason="Supernova won't boot on Windows"
    ),
)


def setup_context(context_class, name=None):
    def on_event(event: ServerLifecycleEvent) -> None:
        events.append(event)

    events = []
    context = context_class(name=name)
    for event in ServerLifecycleEvent:
        context.on(event, on_event)
    return context, events


async def get(x):
    if asyncio.iscoroutine(x):
        return await x
    return x


logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def use_caplog(caplog):
    caplog.set_level(logging.INFO)


@pytest.fixture(autouse=True)
def healthcheck_attempts(monkeypatch):
    monkeypatch.setattr(DEFAULT_HEALTHCHECK, "max_attempts", 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_only(executable, context_class):
    context, events = setup_context(context_class)
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    #
    await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert context.boot_future.done()
    assert not context.exit_future.done()


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_and_quit(executable, context_class):
    context, events = setup_context(context_class)
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    #
    await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    #
    await get(context.quit())
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.PROCESS_QUIT,
        ServerLifecycleEvent.QUIT,
    ]
    assert context.boot_future.done()
    assert context.exit_future.done()


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_and_boot(executable, context_class):
    context, events = setup_context(context_class)
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    #
    await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    #
    with pytest.raises(ServerOnline):
        await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_and_quit_and_quit(executable, context_class):
    context, events = setup_context(context_class)
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    #
    await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    #
    await get(context.quit())
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.PROCESS_QUIT,
        ServerLifecycleEvent.QUIT,
    ]
    #
    await get(context.quit())
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.PROCESS_QUIT,
        ServerLifecycleEvent.QUIT,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_and_connect(executable, context_class):
    context, events = setup_context(context_class)
    assert context.boot_status == BootStatus.OFFLINE
    assert not context.is_owner
    #
    await get(context.boot(executable=executable))
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    #
    with pytest.raises(ServerOnline):
        await get(context.connect())
    assert context.boot_status == BootStatus.ONLINE
    assert context.is_owner
    assert events == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_boot_b_cannot_boot(executable, context_class):
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    await get(context_a.boot(maximum_logins=4, executable=executable))
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == []
    #
    with pytest.raises(ServerCannotBoot):
        await get(context_b.boot(maximum_logins=4, executable=executable))
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_PANICKED,
    ]


# scsynth only
@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_too_many_clients(executable, context_class):
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    await get(context_a.boot(maximum_logins=1))
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == []
    #
    with pytest.raises(TooManyClients):
        await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.DISCONNECTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_quit_a(executable, context_class):
    logger.warning("START")
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    logger.warning("BOOT A")
    await get(context_a.boot(maximum_logins=2, executable=executable))
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == []
    #
    logger.warning("CONNECT B")
    await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    logger.warning("PROCESS_QUIT A")
    await get(context_a.quit())
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.PROCESS_QUIT,
        ServerLifecycleEvent.QUIT,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    logger.warning("AWAIT B")
    for _ in range(100):
        await asyncio.sleep(0.1)
        if context_b.boot_status == BootStatus.OFFLINE:
            break
    logger.warning("DONE AWAITING B")
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.PROCESS_QUIT,
        ServerLifecycleEvent.QUIT,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.OSC_PANICKED,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.DISCONNECTED,
    ]
    logger.warning("END")


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_disconnect_b(executable, context_class):
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    await get(context_a.boot(maximum_logins=2, executable=executable))
    await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    await get(context_b.disconnect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_disconnect_a(executable, context_class):
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    await get(context_a.boot(maximum_logins=2, executable=executable))
    await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    with pytest.raises(OwnedServerShutdown):
        await get(context_a.disconnect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_quit_b(executable, context_class):
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    await get(context_a.boot(maximum_logins=2, executable=executable))
    await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    with pytest.raises(UnownedServerShutdown):
        await get(context_b.quit())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_force_quit_b(executable, context_class):
    logger.warning("START")
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    #
    logger.warning("BOOT A")
    await get(context_a.boot(maximum_logins=2, executable=executable))
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == []
    #
    logger.warning("CONNECT B")
    await get(context_b.connect())
    assert context_a.boot_status == BootStatus.ONLINE and context_a.is_owner
    assert context_b.boot_status == BootStatus.ONLINE and not context_b.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    #
    logger.warning("FORCE PROCESS_QUIT B")
    await get(context_b.quit(force=True))
    assert context_b.boot_status == BootStatus.OFFLINE and not context_b.is_owner
    logger.warning("AWAIT A")
    for _ in range(100):
        await asyncio.sleep(0.1)
        if context_a.boot_status == BootStatus.OFFLINE:
            break
    assert context_a.boot_status == BootStatus.OFFLINE and not context_a.is_owner
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.PROCESS_PANICKED,
        ServerLifecycleEvent.OSC_PANICKED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.QUIT,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.OSC_DISCONNECTED,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.QUIT,
    ]
    logger.warning("END")


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_reboot_sticky_options(executable, context_class):
    """
    Options persist across booting and quitting.
    """
    context, _ = setup_context(context_class)
    maximum_node_count = random.randint(1024, 2048)
    await get(
        context.boot(maximum_node_count=maximum_node_count, port=find_free_port())
    )
    assert context.options.maximum_node_count == maximum_node_count
    await get(context.quit())
    assert context.options.maximum_node_count == maximum_node_count
    await get(context.boot(port=find_free_port()))
    assert context.options.maximum_node_count == maximum_node_count
    await get(context.quit())
    assert context.options.maximum_node_count == maximum_node_count


@pytest.mark.asyncio
@pytest.mark.parametrize("executable", ["scsynth", supernova])
@pytest.mark.parametrize("context_class", [AsyncServer, Server])
async def test_boot_a_and_connect_b_and_kill(executable, context_class) -> None:
    logger.warning("START")
    context_a, events_a = setup_context(context_class, name="one")
    context_b, events_b = setup_context(context_class, name="two")
    logger.warning("BOOT A")
    await get(context_a.boot(executable=executable, maximum_logins=2))
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == []
    logger.warning("CONNECT B")
    await get(context_b.connect())
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
    ]
    logger.warning("KILL")
    kill()
    logger.warning("AWAIT A AND B")
    for _ in range(100):
        await asyncio.sleep(0.1)
        if (
            context_a.boot_status == BootStatus.OFFLINE
            and context_b.boot_status == BootStatus.OFFLINE
        ):
            break
    assert events_a == [
        ServerLifecycleEvent.BOOTING,
        ServerLifecycleEvent.PROCESS_BOOTED,
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.BOOTED,
        ServerLifecycleEvent.PROCESS_PANICKED,
        ServerLifecycleEvent.OSC_PANICKED,
        ServerLifecycleEvent.QUITTING,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.DISCONNECTED,
        ServerLifecycleEvent.QUIT,
    ]
    assert events_b == [
        ServerLifecycleEvent.CONNECTING,
        ServerLifecycleEvent.OSC_CONNECTED,
        ServerLifecycleEvent.CONNECTED,
        ServerLifecycleEvent.OSC_PANICKED,
        ServerLifecycleEvent.DISCONNECTING,
        ServerLifecycleEvent.DISCONNECTED,
    ]
    assert context_a.boot_future.done()
    assert context_a.exit_future.done()
    assert context_b.boot_future.done()
    assert context_b.exit_future.done()
    logger.warning("END")
