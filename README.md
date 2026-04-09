# DomoActors-Py

A Production-Ready Actor Model Toolkit for Python

[![License: LGPL-3.0](https://img.shields.io/badge/License-LGPL--3.0-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/pypi-domo--actors-blue.svg)](https://pypi.org/project/domo-actors/)
[![Test Coverage](https://img.shields.io/badge/coverage-86%25-green.svg)](./tests)

## Overview

DomoActors-Py is a sophisticated actor framework for Python that provides:

- **Comprehensive Type Hints**: Full type annotations with Protocol classes for IDE support and static analysis
- **Fault Tolerance**: Hierarchical supervision with configurable strategies
- **Message-Driven Concurrency**: FIFO per-actor mailboxes with async dispatch
- **Flexible Addressing**: UUIDv7 for distributed systems, numeric for simple scenarios
- **Comprehensive Testing**: Observable state, await utilities, dead letter listeners
- **Zero External Dependencies**: Pure Python implementation using only standard library

## Project Status

✅ **Production Ready** - Fully implemented with comprehensive test coverage (197+ tests, 86% coverage)

**Complete Feature Set**:
- ✅ Core actor model (Actor, Protocol, Stage)
- ✅ Hierarchical supervision (Resume, Restart, Stop, Escalate)
- ✅ Self-messaging patterns with recursive mailbox dispatch
- ✅ Bounded and unbounded mailboxes with overflow policies
- ✅ Lifecycle hooks (before_start, after_stop, before_restart, etc.)
- ✅ Scheduling (one-time and repeating tasks)
- ✅ Dead letters handling
- ✅ Observable state for testing
- ✅ Full parity with DomoActors-TS

**Example Applications**:
- ✅ Complete banking system with interactive CLI
- ✅ Transaction coordination with retry logic
- ✅ Context-aware error handling

## Quick Start

### Installation

Install DomoActors-Py from PyPI using pip:

```bash
pip install domo-actors
```

**Requirements**: Python 3.10 or higher (no external dependencies!)

#### Alternative: Install from Source

For development or the latest unreleased features:

```bash
git clone https://github.com/VaughnVernon/DomoActors-Py.git
cd DomoActors-Py
pip install -e .
```

#### Verify Installation

```python
from domo_actors import stage, Actor, Protocol
print("DomoActors-Py installed successfully!")
```

### Basic Example

```python
import asyncio
from domo_actors import Actor, ActorProtocol, Protocol, ProtocolInstantiator
from domo_actors import Definition, stage, Uuid7Address


# 1. Define the protocol interface
class Counter(ActorProtocol):
    async def increment(self) -> None: ...
    async def get_value(self) -> int: ...


# 2. Implement the actor
class CounterActor(Actor):
    def __init__(self):
        super().__init__()
        self._count = 0

    async def increment(self) -> None:
        self._count += 1

    async def get_value(self) -> int:
        return self._count


# 3. Create protocol instantiator
class CounterInstantiator(ProtocolInstantiator):
    def instantiate(self, definition: Definition) -> Actor:
        return CounterActor()


class CounterProtocol(Protocol):
    def type(self) -> str:
        return "Counter"

    def instantiator(self) -> ProtocolInstantiator:
        return CounterInstantiator()


# 4. Use the actor
async def main():
    # Create actor (stage() returns singleton instance)
    counter: Counter = stage().actor_for(
        CounterProtocol(),
        Definition("Counter", Uuid7Address(), ())
    )

    # Use actor
    await counter.increment()
    await counter.increment()
    value = await counter.get_value()
    print(f"Count: {value}")  # Output: Count: 2

    # Cleanup
    await stage().close()


if __name__ == "__main__":
    asyncio.run(main())
```

## Core Concepts

### Actors

Actors are the fundamental unit of computation. They:
- Process messages sequentially through their mailbox
- Maintain private state
- Can create child actors
- Never share state directly

### Messages

Messages are asynchronous and delivered via FIFO mailboxes. DomoActors uses a dynamic proxy pattern that automatically converts method calls into messages.

### Supervision

Actors are organized in a hierarchy. When an actor fails, its supervisor decides what to do:
- **Restart**: Create a new instance
- **Resume**: Continue processing messages
- **Stop**: Terminate the actor
- **Escalate**: Pass the decision to the parent supervisor

### Lifecycle Hooks

Actors provide lifecycle hooks for customization:
- `before_start()`: Initialize actor state
- `before_stop()`: Cleanup before termination
- `before_restart(reason)`: Cleanup before restart
- `after_restart()`: Re-initialize after restart

## Features

### Dynamic Proxy Pattern

DomoActors uses Python's `__getattr__` magic method to implement a dynamic proxy pattern similar to JavaScript's Proxy API:

```python
# Method calls are automatically converted to messages
await actor.do_something(arg1, arg2)
# Behind the scenes:
# 1. Creates a DeferredPromise
# 2. Wraps call in a LocalMessage
# 3. Enqueues in mailbox
# 4. Returns promise to caller
```

### Mailbox Types

**ArrayMailbox**: Unbounded FIFO queue
```python
from domo_actors import ArrayMailbox
mailbox = ArrayMailbox()
```

**BoundedMailbox**: Capacity-limited with overflow policies
```python
from domo_actors import BoundedMailbox, OverflowPolicy

mailbox = BoundedMailbox(
    capacity=100,
    overflow_policy=OverflowPolicy.DROP_OLDEST
)
```

### Fault Tolerance

Configure supervision strategies:

```python
from domo_actors import DefaultSupervisor, SupervisionStrategy, SupervisionScope

class MySupervisor(DefaultSupervisor):
    async def supervision_strategy(self) -> SupervisionStrategy:
        return CustomStrategy()

class CustomStrategy(SupervisionStrategy):
    def intensity(self) -> int:
        return 5  # Allow 5 restarts

    def period(self) -> int:
        return 10000  # Within 10 seconds

    def scope(self) -> SupervisionScope:
        return SupervisionScope.ONE  # Only failed actor
```

### Scheduling

Schedule tasks using the built-in scheduler:

```python
from datetime import timedelta
from domo_actors import stage

scheduler = stage().scheduler()

# Schedule once
scheduler.schedule_once(
    delay=timedelta(seconds=5),
    action=lambda: print("Executed!")
)

# Schedule repeated
scheduler.schedule_repeat(
    initial_delay=timedelta(seconds=1),
    interval=timedelta(seconds=5),
    action=lambda: print("Tick!")
)
```

## Testing

DomoActors provides testing utilities:

```python
from domo_actors.actors.testkit import await_assert, await_state_value

async def test_actor():
    # Wait for assertion to pass
    await await_assert(
        lambda: assert_something(),
        timeout=2.0
    )

    # Wait for state value
    await await_state_value(
        actor,
        "status",
        "completed",
        timeout=2.0
    )
```

## Examples

See the `examples/` directory for complete examples:

### Counter Example

Basic actor creation and message passing demonstrating:
- Protocol definition
- Actor implementation
- Message passing
- Async/await patterns

### Bank Example (Production-Grade)

A complete banking system with interactive CLI (`examples/bank/bank.py`) demonstrating:

**Core Features**:
- Account management (open, deposit, withdraw)
- Inter-account transfers with 5-phase coordination
- Transaction history with self-messaging pattern
- Exponential backoff retry logic

**Advanced Patterns**:
- **Hierarchical actors**: Bank → Account → TransactionHistory
- **Three supervisor types**: BankSupervisor, AccountSupervisor, TransferSupervisor
- **Context-aware error handling**: Custom error messages with request details
- **Self-messaging**: Actors sending messages to themselves for state consistency
- **"Let it crash" philosophy**: Validation errors handled by supervisors

**Run the example**:
```bash
cd examples/bank
python bank.py
```

The bank example is functionally equivalent to the TypeScript version, demonstrating full parity between implementations.

## Architecture

```
┌─────────────────────────────────────┐
│         LocalStage                  │
│  ┌───────────────────────────────┐  │
│  │    PrivateRootActor           │  │
│  │      ┌─────────────────────┐  │  │
│  │      │  PublicRootActor    │  │  │
│  │      │    ┌──────────┐     │  │  │
│  │      │    │  User    │     │  │  │
│  │      │    │  Actors  │     │  │  │
│  │      │    └──────────┘     │  │  │
│  │      └─────────────────────┘  │  │
│  └───────────────────────────────┘  │
│                                     │
│  Directory (Actor Registry)         │
│  Scheduler                          │
│  DeadLetters                        │
│  Supervisors                        │
└─────────────────────────────────────┘
```

## Design Principles

1. **Correctness First**: Type-safe interfaces, strict async/await patterns
2. **Fault Tolerance**: Hierarchical supervision
3. **Developer Productivity**: Protocol interfaces, lifecycle hooks, testing utilities
4. **Zero Dependencies**: Pure Python using only standard library

## Comparison with TypeScript Version

DomoActors-Py is a faithful port of [DomoActors-TS](https://github.com/VaughnVernon/DomoActors-TS) with Python-specific adaptations:

| Feature | TypeScript | Python |
|---------|-----------|--------|
| **Proxy Pattern** | ES6 Proxy API | `__getattr__` magic method |
| **Async Model** | Promises | asyncio Futures |
| **Concurrency** | Single-threaded event loop (async/await) | Single-threaded event loop (async/await) |
| **Type System** | Compile-time static typing | Runtime type hints (PEP 484) |
| **Type Checking** | Built-in (tsc) | Optional tools (mypy, pyright) |
| **IDE Support** | Full IntelliSense | Full IntelliSense with type hints |
| **Stage Access** | `stage()` singleton | `stage()` singleton |
| **Mailbox Dispatch** | Recursive dispatch | Recursive dispatch |
| **Self-Messaging** | `this.selfAs<T>()` | `self.self_as(T)` |
| **Supervision** | Hierarchical supervisors | Hierarchical supervisors |
| **Collections** | Map/Set | dict/set |
| **Actor Lifecycle** | Hooks (beforeStart, etc.) | Hooks (before_start, etc.) |

### Architectural Parity

Both implementations share the same core architecture:

- **Actor hierarchy**: PrivateRootActor → PublicRootActor → User actors
- **Supervision strategies**: Resume, Restart, Stop, Escalate
- **Message delivery**: FIFO per-actor mailboxes
- **Address types**: UUIDv7 for distributed, numeric for simple scenarios
- **Zero external dependencies**: Both use only standard library features

### Python-Specific Features

- **Context managers**: Can use `async with` for resource management
- **Type hints**: Comprehensive PEP 484 type annotations throughout the codebase
- **Static type checking**: Compatible with mypy, pyright, and IDE type checkers
- **Protocol classes**: Structural typing similar to TypeScript interfaces
- **AsyncIO integration**: Native asyncio support, works with existing async code
- **Testing**: pytest-asyncio integration for async test cases

### Concurrency Model

DomoActors-Py uses **single-threaded async/await**, just like JavaScript/TypeScript:

```python
# Single event loop thread
async def actor_method(self):
    await self.some_operation()  # Yields to event loop
    # Continues on same thread
```

**Key Points**:
- ✅ Single-threaded event loop (like JavaScript)
- ✅ Cooperative multitasking at `await` points
- ✅ No parallelism, only concurrency
- ✅ Actors process messages sequentially
- ✅ Perfect parity with DomoActors-TS behavior

**Note**: Python *does* support multi-threading (`threading` module) and multi-processing (`multiprocessing` module), but DomoActors-Py uses pure `asyncio` to maintain identical semantics with the TypeScript version.

### Type Hints and Static Analysis

DomoActors-Py includes comprehensive type hints:

```python
# Full type annotations
def actor_for(
    self,
    protocol: Protocol,
    definition: Definition,
    parent: Optional[Actor] = None,
    supervisor_name: Optional[str] = None
) -> T:
    ...

# Generic type variables
T = TypeVar('T')

# Protocol classes for structural typing
class Counter(ActorProtocol):
    async def increment(self) -> None: ...
    async def get_value(self) -> int: ...
```

**Benefits**:
- ✅ IDE autocomplete and IntelliSense
- ✅ Catch type errors before runtime with mypy/pyright
- ✅ Self-documenting code
- ✅ Refactoring safety

**Check types statically**:
```bash
mypy domo_actors  # Type check the library
```

## Requirements

- Python 3.10 or higher
- No external dependencies for core functionality
- `pytest` and `pytest-asyncio` for running tests

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black domo_actors tests examples

# Type check
mypy domo_actors

# Lint
ruff check domo_actors tests examples
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Issues**: https://github.com/VaughnVernon/DomoActors-Py/issues
- **Discussions**: https://github.com/VaughnVernon/DomoActors-Py/discussions
- **Documentation**: See `docs/` directory

## Acknowledgments

DomoActors-Py is inspired by and builds upon concepts from:
- **XOOM/Actors** (Java actor framework by Vaughn Vernon)
- **DomoActors-TS** (TypeScript version)

## License

GNU Lesser General Public License v3.0 (LGPL-3.0)

See: ./LICENSE.md


Copyright © 2012-2026 Vaughn Vernon. All rights reserved.
Copyright © 2012-2026 Kalele, Inc. All rights reserved.

## About the Creator and Author

**Vaughn Vernon**

- **Creator of the XOOM Platform**
  - [Product conceived 10 years before GenAI was hip hype](https://kalele.io/xoom-platform/)
  - [Docs](https://docs.vlingo.io)
  - [Actors Docs](https://docs.vlingo.io/xoom-actors)
  - [Reference implementation in Java](https://github.com/vlingo)
- **Books**:
  - [_Implementing Domain-Driven Design_](https://www.informit.com/store/implementing-domain-driven-design-9780321834577)
  - [_Reactive Messaging Patterns with the Actor Model_](https://www.informit.com/store/reactive-messaging-patterns-with-the-actor-model-applications-9780133846881)
  - [_Domain-Driven Design Distilled_](https://www.informit.com/store/domain-driven-design-distilled-9780134434421)
  - [_Strategic Monoliths and Microservices_](https://www.informit.com/store/strategic-monoliths-and-microservices-driving-innovation-9780137355464)
- **Live and In-Person Training**:
  - [_Implementing Domain-Driven Design_ and others](https://kalele.io/training/)
- *__LiveLessons__* video training:
  - [_Domain-Driven Design Distilled_](https://www.informit.com/store/domain-driven-design-livelessons-video-training-9780134597324)
    - Available on the [O'Reilly Learning Platform](https://www.oreilly.com/videos/domain-driven-design-distilled/9780134593449/)
  - [_Strategic Monoliths and Microservices_](https://www.informit.com/store/strategic-monoliths-and-microservices-video-course-9780138268237)
    - Available on the [O'Reilly Learning Platform](https://www.oreilly.com/videos/strategic-monoliths-and/9780138268251/)
- **Curator and Editor**: Pearson Addison-Wesley Signature Series
  - [Vaughn Vernon Signature Series](https://informit.com/awss/vernon)
- **Personal website**: https://vaughnvernon.com
