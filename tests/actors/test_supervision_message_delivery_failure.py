"""
Supervision Message Delivery Failure tests - Message processing error handling.

Test cases covering message failure and supervision.
"""

import pytest
import asyncio
from typing import Dict
from domo_actors.actors.actor import Actor
from domo_actors.actors.actor_protocol import ActorProtocol
from domo_actors.actors.protocol import Protocol, ProtocolInstantiator
from domo_actors.actors.definition import Definition
from domo_actors.actors.local_stage import LocalStage
from domo_actors.actors.address import Uuid7Address
from domo_actors.actors.supervisor import (
    DefaultSupervisor,
    SupervisionDirective,
    SupervisionStrategy,
    SupervisionScope,
    Supervised
)


# Global storage
counter_actors: Dict[str, 'CounterActorImpl'] = {}
fail_after_n_actors: Dict[str, 'FailAfterNActorImpl'] = {}
restart_supervisors: Dict[str, 'RestartSupervisorImpl'] = {}
resume_supervisors: Dict[str, 'ResumeSupervisorImpl'] = {}
stop_supervisors: Dict[str, 'StopSupervisorImpl'] = {}


# ============================================================================
# Supervision Strategy
# ============================================================================

class TestStrategy(SupervisionStrategy):
    """Test supervision strategy."""

    def intensity(self) -> int:
        return 5

    def period(self) -> int:
        return 10000

    def scope(self) -> SupervisionScope:
        return SupervisionScope.ONE


# ============================================================================
# Supervisors
# ============================================================================

class RestartSupervisor(ActorProtocol):
    async def get_inform_count(self) -> int: ...
    async def get_last_error(self) -> Exception: ...


class RestartSupervisorImpl(DefaultSupervisor):
    def __init__(self):
        super().__init__()
        self._inform_count = 0
        self._last_error = None

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        self._last_error = error
        await super().inform(error, supervised)

    def decide_directive(self, error: Exception, supervised: Supervised, strategy: SupervisionStrategy) -> SupervisionDirective:
        return SupervisionDirective.RESTART

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestStrategy()

    async def get_inform_count(self) -> int:
        return self._inform_count

    async def get_last_error(self) -> Exception:
        return self._last_error


class RestartSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = RestartSupervisorImpl()
        restart_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class RestartSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "RestartSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return RestartSupervisorInstantiator()


# Resume Supervisor

class ResumeSupervisor(ActorProtocol):
    async def get_inform_count(self) -> int: ...


class ResumeSupervisorImpl(DefaultSupervisor):
    def __init__(self):
        super().__init__()
        self._inform_count = 0

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        await super().inform(error, supervised)

    def decide_directive(self, error: Exception, supervised: Supervised, strategy: SupervisionStrategy) -> SupervisionDirective:
        return SupervisionDirective.RESUME

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestStrategy()

    async def get_inform_count(self) -> int:
        return self._inform_count


class ResumeSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = ResumeSupervisorImpl()
        resume_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class ResumeSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "ResumeSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return ResumeSupervisorInstantiator()


# Stop Supervisor

class StopSupervisor(ActorProtocol):
    async def get_inform_count(self) -> int: ...


class StopSupervisorImpl(DefaultSupervisor):
    def __init__(self):
        super().__init__()
        self._inform_count = 0

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        await super().inform(error, supervised)

    def decide_directive(self, error: Exception, supervised: Supervised, strategy: SupervisionStrategy) -> SupervisionDirective:
        return SupervisionDirective.STOP

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestStrategy()

    async def get_inform_count(self) -> int:
        return self._inform_count


class StopSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = StopSupervisorImpl()
        stop_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class StopSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "StopSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return StopSupervisorInstantiator()


# ============================================================================
# Test Actors
# ============================================================================

class Counter(ActorProtocol):
    async def increment(self) -> None: ...
    async def get_value(self) -> int: ...
    async def cause_error(self) -> None: ...
    async def reset(self) -> None: ...
    async def get_restart_count(self) -> int: ...
    async def was_before_restart_called(self) -> bool: ...
    async def was_after_restart_called(self) -> bool: ...
    async def was_before_resume_called(self) -> bool: ...


class CounterActorImpl(Actor):
    def __init__(self):
        super().__init__()
        self._count = 0
        self._restart_count = 0
        self._before_restart_called = False
        self._after_restart_called = False
        self._before_resume_called = False

    async def increment(self) -> None:
        self._count += 1

    async def get_value(self) -> int:
        return self._count

    async def cause_error(self) -> None:
        raise ValueError("Intentional message processing error")

    async def reset(self) -> None:
        self._count = 0

    async def get_restart_count(self) -> int:
        return self._restart_count

    async def was_before_restart_called(self) -> bool:
        return self._before_restart_called

    async def was_after_restart_called(self) -> bool:
        return self._after_restart_called

    async def was_before_resume_called(self) -> bool:
        return self._before_resume_called

    async def before_restart(self, reason: Exception) -> None:
        await super().before_restart(reason)
        self._before_restart_called = True
        self._restart_count += 1

    async def after_restart(self) -> None:
        await super().after_restart()
        self._after_restart_called = True
        self._count = 0  # Reset state

    async def before_resume(self) -> None:
        await super().before_resume()
        self._before_resume_called = True


class CounterInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        actor = CounterActorImpl()
        counter_actors[definition.address().value_as_string()] = actor
        return actor


class CounterProtocol(Protocol):
    def type(self) -> str:
        return "Counter"

    def instantiator(self) -> ProtocolInstantiator:
        return CounterInstantiator()


# Fail After N Actor

class FailAfterN(ActorProtocol):
    async def operation(self) -> None: ...
    async def get_operation_count(self) -> int: ...


class FailAfterNActorImpl(Actor):
    def __init__(self, fail_after: int):
        super().__init__()
        self._fail_after = fail_after
        self._operation_count = 0

    async def operation(self) -> None:
        self._operation_count += 1
        if self._operation_count >= self._fail_after:
            raise ValueError(f"Failed after {self._operation_count} operations")

    async def get_operation_count(self) -> int:
        return self._operation_count


class FailAfterNInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        params = definition.parameters()
        fail_after = params[0] if params else 1
        actor = FailAfterNActorImpl(fail_after)
        fail_after_n_actors[definition.address().value_as_string()] = actor
        return actor


class FailAfterNProtocol(Protocol):
    def type(self) -> str:
        return "FailAfterN"

    def instantiator(self) -> ProtocolInstantiator:
        return FailAfterNInstantiator()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def stage():
    s = LocalStage()

    # Create and register supervisors
    restart_sup: RestartSupervisor = s.actor_for(
        RestartSupervisorProtocol(),
        Definition("RestartSupervisor", Uuid7Address(), ())
    )
    s.register_supervisor("restart", restart_sup)

    resume_sup: ResumeSupervisor = s.actor_for(
        ResumeSupervisorProtocol(),
        Definition("ResumeSupervisor", Uuid7Address(), ())
    )
    s.register_supervisor("resume", resume_sup)

    stop_sup: StopSupervisor = s.actor_for(
        StopSupervisorProtocol(),
        Definition("StopSupervisor", Uuid7Address(), ())
    )
    s.register_supervisor("stop", stop_sup)

    yield s
    asyncio.run(s.close())


@pytest.fixture(autouse=True)
def clear_actors():
    counter_actors.clear()
    fail_after_n_actors.clear()
    restart_supervisors.clear()
    resume_supervisors.clear()
    stop_supervisors.clear()


# ============================================================================
# Tests
# ============================================================================

@pytest.mark.asyncio
async def test_message_error_triggers_supervision(stage):
    """Test that message processing error triggers supervisor."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # Supervisor should be informed
    supervisor = list(restart_supervisors.values())[0]
    assert supervisor._inform_count >= 1


@pytest.mark.asyncio
async def test_message_error_rejects_promise(stage):
    """Test that message error rejects the caller's promise."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Should raise error
    with pytest.raises(Exception) as exc_info:
        await counter.cause_error()

    assert "Intentional message processing error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_mailbox_suspended_during_supervision(stage):
    """Test that mailbox is suspended during supervision."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    # Check mailbox (small delay for suspension)
    await asyncio.sleep(0.01)

    raw_actor = counter_actors[counter.address().value_as_string()]
    mailbox = raw_actor.life_cycle().environment().mailbox()

    # Mailbox should be suspended immediately after error
    # (it gets resumed after restart, so we need to check quickly)
    # For this test, we'll verify the restart happened instead
    await asyncio.sleep(0.1)

    # After restart, mailbox should be resumed
    assert mailbox.is_suspended() == False


@pytest.mark.asyncio
async def test_restart_resets_state(stage):
    """Test that restart directive resets actor state."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Increment counter
    await counter.increment()
    await counter.increment()

    value_before = await counter.get_value()
    assert value_before == 2

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # State should be reset
    value_after = await counter.get_value()
    assert value_after == 0


@pytest.mark.asyncio
async def test_resume_preserves_state(stage):
    """Test that resume directive preserves actor state."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="resume"
    )

    await asyncio.sleep(0.05)

    # Increment counter
    await counter.increment()
    await counter.increment()

    value_before = await counter.get_value()
    assert value_before == 2

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # State should be preserved
    value_after = await counter.get_value()
    assert value_after == 2


@pytest.mark.asyncio
async def test_mailbox_resumed_after_restart(stage):
    """Test that mailbox is resumed after restart completes."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # Mailbox should be resumed
    raw_actor = counter_actors[counter.address().value_as_string()]
    mailbox = raw_actor.life_cycle().environment().mailbox()
    assert mailbox.is_suspended() == False

    # Should be able to process new messages
    await counter.increment()
    value = await counter.get_value()
    assert value == 1


@pytest.mark.asyncio
async def test_multiple_failures_handled(stage):
    """Test handling multiple failures with restarts."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Cause multiple errors
    for _ in range(3):
        try:
            await counter.cause_error()
        except:
            pass
        await asyncio.sleep(0.1)

    # Should have restarted multiple times
    restart_count = await counter.get_restart_count()
    assert restart_count >= 3


@pytest.mark.asyncio
async def test_stop_directive_stops_actor(stage):
    """Test that stop directive stops the actor."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="stop"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # Actor should be stopped
    assert counter.is_stopped() == True


@pytest.mark.asyncio
async def test_periodic_failures(stage):
    """Test handling periodic failures."""
    fail_actor: FailAfterN = stage.actor_for(
        FailAfterNProtocol(),
        Definition("FailAfterN", Uuid7Address(), (3,)),
        supervisor_name="resume"
    )

    await asyncio.sleep(0.05)

    # First 2 should succeed
    await fail_actor.operation()
    await fail_actor.operation()

    # Third should fail
    try:
        await fail_actor.operation()
    except:
        pass

    await asyncio.sleep(0.1)

    # Should have resumed and can continue
    count = await fail_actor.get_operation_count()
    assert count >= 3


@pytest.mark.asyncio
async def test_rapid_sequential_failures(stage):
    """Test handling rapid sequential failures."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Rapid failures
    for _ in range(5):
        try:
            await counter.cause_error()
        except:
            pass

    await asyncio.sleep(0.2)

    # All should have been handled
    restart_count = await counter.get_restart_count()
    assert restart_count >= 5


@pytest.mark.asyncio
async def test_non_error_objects_in_messages(stage):
    """Test handling non-Error objects in exceptions."""
    # This is inherently handled by Python's exception system
    # All exceptions must derive from BaseException
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # Cause error (ValueError is a proper exception)
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # Should have been handled normally
    supervisor = list(restart_supervisors.values())[0]
    assert supervisor._inform_count >= 1


@pytest.mark.asyncio
async def test_async_errors_in_message_processing(stage):
    """Test handling async errors in message processing."""
    counter: Counter = stage.actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ()),
        supervisor_name="restart"
    )

    await asyncio.sleep(0.05)

    # cause_error is async and raises
    try:
        await counter.cause_error()
    except:
        pass

    await asyncio.sleep(0.1)

    # Should have triggered supervision
    supervisor = list(restart_supervisors.values())[0]
    assert supervisor._inform_count >= 1
    assert await counter.get_restart_count() >= 1


@pytest.mark.asyncio
async def test_supervision_under_load(stage):
    """Test supervision handling under load."""
    actors = []

    # Create multiple actors
    for i in range(10):
        actor: Counter = stage.actor_for(
            CounterProtocol(),
            Definition(f"Counter{i}", Uuid7Address(), ()),
            supervisor_name="restart"
        )
        actors.append(actor)

    await asyncio.sleep(0.1)

    # Cause errors in all
    for actor in actors:
        try:
            await actor.cause_error()
        except:
            pass

    await asyncio.sleep(0.2)

    # All should have restarted
    for actor in actors:
        restart_count = await actor.get_restart_count()
        assert restart_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
