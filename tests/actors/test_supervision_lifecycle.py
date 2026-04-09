"""
Supervision Lifecycle tests - Supervision directives and strategies.

Test cases covering supervision integration.
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
error_prone_actors: Dict[str, 'ErrorProneActorImpl'] = {}
restarting_supervisors: Dict[str, 'RestartingSupervisorImpl'] = {}
resuming_supervisors: Dict[str, 'ResumingSupervisorImpl'] = {}
stopping_supervisors: Dict[str, 'StoppingSupervisorImpl'] = {}


# ============================================================================
# Custom Supervision Strategies
# ============================================================================

class TestSupervisionStrategy(SupervisionStrategy):
    """Test supervision strategy."""

    def intensity(self) -> int:
        return 5  # Allow 5 restarts

    def period(self) -> int:
        return 10000  # Within 10 seconds

    def scope(self) -> SupervisionScope:
        return SupervisionScope.ONE


# ============================================================================
# Custom Supervisors
# ============================================================================

class RestartingSupervisor(ActorProtocol):
    """Supervisor that always restarts."""
    pass


class RestartingSupervisorImpl(DefaultSupervisor):
    """Supervisor that returns Restart directive."""

    def __init__(self):
        super().__init__()
        self._inform_count = 0
        self._last_error = None

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        self._last_error = error
        await super().inform(error, supervised)

    def decide_directive(
        self,
        error: Exception,
        supervised: Supervised,
        strategy: SupervisionStrategy
    ) -> SupervisionDirective:
        return SupervisionDirective.RESTART

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestSupervisionStrategy()


class RestartingSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = RestartingSupervisorImpl()
        restarting_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class RestartingSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "RestartingSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return RestartingSupervisorInstantiator()


# Resuming Supervisor

class ResumingSupervisor(ActorProtocol):
    """Supervisor that always resumes."""
    pass


class ResumingSupervisorImpl(DefaultSupervisor):
    """Supervisor that returns Resume directive."""

    def __init__(self):
        super().__init__()
        self._inform_count = 0

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        await super().inform(error, supervised)

    def decide_directive(
        self,
        error: Exception,
        supervised: Supervised,
        strategy: SupervisionStrategy
    ) -> SupervisionDirective:
        return SupervisionDirective.RESUME

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestSupervisionStrategy()


class ResumingSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = ResumingSupervisorImpl()
        resuming_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class ResumingSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "ResumingSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return ResumingSupervisorInstantiator()


# Stopping Supervisor

class StoppingSupervisor(ActorProtocol):
    """Supervisor that always stops."""
    pass


class StoppingSupervisorImpl(DefaultSupervisor):
    """Supervisor that returns Stop directive."""

    def __init__(self):
        super().__init__()
        self._inform_count = 0

    async def inform(self, error: Exception, supervised: Supervised) -> None:
        self._inform_count += 1
        await super().inform(error, supervised)

    def decide_directive(
        self,
        error: Exception,
        supervised: Supervised,
        strategy: SupervisionStrategy
    ) -> SupervisionDirective:
        return SupervisionDirective.STOP

    async def supervision_strategy(self) -> SupervisionStrategy:
        return TestSupervisionStrategy()


class StoppingSupervisorInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        supervisor = StoppingSupervisorImpl()
        stopping_supervisors[definition.address().value_as_string()] = supervisor
        return supervisor


class StoppingSupervisorProtocol(Protocol):
    def type(self) -> str:
        return "StoppingSupervisor"

    def instantiator(self) -> ProtocolInstantiator:
        return StoppingSupervisorInstantiator()


# ============================================================================
# Error Prone Actor
# ============================================================================

class ErrorProne(ActorProtocol):
    """Actor that can fail in various ways."""
    async def cause_error(self) -> None: ...
    async def get_value(self) -> int: ...
    async def was_before_restart_called(self) -> bool: ...
    async def was_after_restart_called(self) -> bool: ...
    async def was_before_resume_called(self) -> bool: ...


class ErrorProneActorImpl(Actor):
    """Actor that fails and tracks lifecycle hooks."""

    def __init__(self):
        super().__init__()
        self._value = 0
        self._before_restart_called = False
        self._after_restart_called = False
        self._before_resume_called = False

    async def cause_error(self) -> None:
        raise ValueError("Intentional error for testing")

    async def get_value(self) -> int:
        return self._value

    async def was_before_restart_called(self) -> bool:
        return self._before_restart_called

    async def was_after_restart_called(self) -> bool:
        return self._after_restart_called

    async def was_before_resume_called(self) -> bool:
        return self._before_resume_called

    async def before_restart(self, reason: Exception) -> None:
        await super().before_restart(reason)
        self._before_restart_called = True

    async def after_restart(self) -> None:
        await super().after_restart()
        self._after_restart_called = True
        self._value = 0  # Reset on restart

    async def before_resume(self) -> None:
        await super().before_resume()
        self._before_resume_called = True


class ErrorProneInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        actor = ErrorProneActorImpl()
        error_prone_actors[definition.address().value_as_string()] = actor
        return actor


class ErrorProneProtocol(Protocol):
    def type(self) -> str:
        return "ErrorProne"

    def instantiator(self) -> ProtocolInstantiator:
        return ErrorProneInstantiator()


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def stage():
    """Create stage with supervisors."""
    s = LocalStage()

    # Create supervisors
    restart_sup: RestartingSupervisor = s.actor_for(
        RestartingSupervisorProtocol(),
        Definition("RestartingSupervisor", Uuid7Address(), ())
    )

    resume_sup: ResumingSupervisor = s.actor_for(
        ResumingSupervisorProtocol(),
        Definition("ResumingSupervisor", Uuid7Address(), ())
    )

    stop_sup: StoppingSupervisor = s.actor_for(
        StoppingSupervisorProtocol(),
        Definition("StoppingSupervisor", Uuid7Address(), ())
    )

    # Register supervisors
    s.register_supervisor("restarting", restart_sup)
    s.register_supervisor("resuming", resume_sup)
    s.register_supervisor("stopping", stop_sup)

    yield s
    asyncio.run(s.close())


@pytest.fixture(autouse=True)
def clear_actors():
    """Clear global storage."""
    error_prone_actors.clear()
    restarting_supervisors.clear()
    resuming_supervisors.clear()
    stopping_supervisors.clear()


# ============================================================================
# Tests
# ============================================================================

@pytest.mark.asyncio
async def test_restart_directive_calls_lifecycle_hooks(stage):
    """Test that Restart directive calls beforeRestart and afterRestart."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="restarting"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for supervision
    await asyncio.sleep(0.1)

    # Verify hooks were called
    assert await actor.was_before_restart_called() == True
    assert await actor.was_after_restart_called() == True


@pytest.mark.asyncio
async def test_restart_directive_resets_state(stage):
    """Test that Restart directive resets actor state."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="restarting"
    )

    await asyncio.sleep(0.05)

    # Get raw actor and set value
    raw_actor = error_prone_actors[actor.address().value_as_string()]
    raw_actor._value = 42

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for restart
    await asyncio.sleep(0.1)

    # Value should be reset to 0
    value = await actor.get_value()
    assert value == 0


@pytest.mark.asyncio
async def test_resume_directive_preserves_state(stage):
    """Test that Resume directive preserves actor state."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="resuming"
    )

    await asyncio.sleep(0.05)

    # Set value
    raw_actor = error_prone_actors[actor.address().value_as_string()]
    raw_actor._value = 42

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for resume
    await asyncio.sleep(0.1)

    # Value should be preserved
    value = await actor.get_value()
    assert value == 42


@pytest.mark.asyncio
async def test_resume_directive_calls_before_resume(stage):
    """Test that Resume directive calls beforeResume hook."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="resuming"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for resume
    await asyncio.sleep(0.1)

    # Verify hook was called
    assert await actor.was_before_resume_called() == True


@pytest.mark.asyncio
async def test_stop_directive_stops_actor(stage):
    """Test that Stop directive stops the actor."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="stopping"
    )

    await asyncio.sleep(0.05)

    assert actor.is_stopped() == False

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for stop
    await asyncio.sleep(0.1)

    # Actor should be stopped
    assert actor.is_stopped() == True


@pytest.mark.asyncio
async def test_supervisor_informed_of_failures(stage):
    """Test that supervisor is informed of actor failures."""
    actor: ErrorProne = stage.actor_for(
        ErrorProneProtocol(),
        Definition("ErrorProne", Uuid7Address(), ()),
        supervisor_name="restarting"
    )

    await asyncio.sleep(0.05)

    # Cause error
    try:
        await actor.cause_error()
    except:
        pass

    # Wait for supervision
    await asyncio.sleep(0.1)

    # Find supervisor
    supervisor = None
    for sup in restarting_supervisors.values():
        if sup._inform_count > 0:
            supervisor = sup
            break

    assert supervisor is not None
    assert supervisor._inform_count >= 1
    assert supervisor._last_error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
