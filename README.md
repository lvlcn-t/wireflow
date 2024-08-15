# Wireflow - DI Container for Python

<!-- markdownlint-disable MD033 -->
<p align="center">
    <a href="https://pypi.org/project/wireflow/" title="PyPI Version"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/wireflow"></a>
    <a href="https://pypi.org/project/wireflow/" title="Supported Python Versions"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/wireflow"></a>
    <a href="/../../commits/" title="Last Commit"><img alt="Last Commit" src="https://img.shields.io/github/last-commit/lvlcn-t/wireflow?style=flat"></a>
    <a href="/../../issues" title="Open Issues"><img alt="Open Issues" src="https://img.shields.io/github/issues/lvlcn-t/wireflow?style=flat"></a>
</p>
<!-- markdownlint-enable MD033 -->

- [What is Wireflow?](#what-is-wireflow)
  - [Why Use Dependency Injection?](#why-use-dependency-injection)
  - [Key Features of Wireflow](#key-features-of-wireflow)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Advanced Usage](#advanced-usage)
  - [Example with Interface and Lifecycle Hooks](#example-with-interface-and-lifecycle-hooks)
  - [What’s Happening Here?](#whats-happening-here)
- [Code of Conduct](#code-of-conduct)
- [Working Language](#working-language)
- [Support and Feedback](#support-and-feedback)
- [How to Contribute](#how-to-contribute)
- [Licensing](#licensing)

## What is Wireflow?

Wireflow is a simple yet powerful **Dependency Injection (DI)** container for Python. It helps you manage and organize dependencies in your Python applications, making your code cleaner, more modular, and easier to maintain.

Whether you're building a small script or a large application, Wireflow lets you register, resolve, and inject dependencies effortlessly, avoiding common pitfalls like tightly coupled code or manual dependency management.

### Why Use Dependency Injection?

Dependency Injection is a design pattern used to implement Inversion of Control (IoC) between classes and their dependencies. Instead of creating dependencies manually within a class, you "inject" them from the outside. This makes your code more flexible and easier to test.

### Key Features of Wireflow

- **Easy to Use**: Simple API that anyone can pick up quickly.
- **Singleton Support**: Manage dependencies as singletons to ensure only one instance exists.
- **Automatic Injection**: Use the `inject` decorator to automatically inject dependencies into your functions.
- **Lifecycle Hooks**: Define custom initialization and destruction behaviors for your dependencies.
- **Scoped Dependencies**: Manage dependencies within specific scopes, like per-request or per-session.

## Installation

To install Wireflow, simply run:

```bash
pip install wireflow
```

And import it into your Python code:

```python
import wireflow
```

## Quick Start

Getting started with Wireflow is straightforward. Here’s a basic example:

```python
import asyncio

from wireflow import container


class Greeter:
    def greet(self) -> str:
        return "Hello, World!"


async def main() -> None:
    # Register the Greeter class as a dependency
    await container.provide(
        dependency=Greeter(),
        singleton=True,  # Ensures only one instance is created
    )

    # Resolve the dependency and use it
    greeter = await container.resolve(Greeter)
    print(greeter.greet())


# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

In this example, we:

1. **Register** the `Greeter` class as a dependency in the container.
2. **Resolve** the dependency when needed.
3. **Use** the resolved dependency.

## Advanced Usage

Wireflow's flexibility shines in more complex scenarios, where you might need to work with interfaces, manage lifecycles, or inject dependencies automatically.

### Example with Interface and Lifecycle Hooks

Let’s look at a more advanced example:

```python
from __future__ import annotations

import asyncio
import abc

from wireflow import container, inject, Provide

# Define a greeter interface
class Greeter(abc.ABC):
    @abc.abstractmethod
    def greet(self) -> str: ...


# Define a service that implements the greeter interface
class WelcomeService(Greeter):
    def greet(self) -> str:
        return "Hello from MyService!"

    # Define static methods for initialization and destruction hooks
    @staticmethod
    async def on_init(service: WelcomeService):
        print(f"Service {service.__class__.__name__} initialized")

    @staticmethod
    async def on_destroy(service: WelcomeService):
        print(f"Service {service.__class__.__name__} destroyed")


async def main() -> None:
    # Register the service with lifecycle hooks and a request scope
    await container.provide(
        dependency=WelcomeService(),
        singleton=True,
        interface=Greeter,  # Registering as the Greeter interface
        on_init=WelcomeService.on_init,
        on_destroy=WelcomeService.on_destroy,
        scope="request",  # Scoped to "request"
    )

    # Call a function without manually passing the service
    await say_hello()

    # Destroy the request scope after use
    await container.destroy_scope("request")


# Function that automatically receives the injected service
@inject
async def say_hello(service: Greeter = Provide[Greeter]) -> None:
    print(service.greet())


# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

### What’s Happening Here?

1. **Interface Definition**: We define a `Greeter` interface using Python’s `abc` module.
2. **Service Implementation**: The `WelcomeService` class implements the `Greeter` interface.
3. **Lifecycle Hooks**: `on_init` and `on_destroy` methods are defined to perform actions when the service is initialized or destroyed.
4. **Dependency Registration**: The `WelcomeService` is registered with the container as a singleton under the `Greeter` interface.
5. **Automatic Injection**: The `say_hello` function receives the `WelcomeService` instance automatically, thanks to the `inject` decorator.
6. **Scope Management**: The service is scoped to a "request", and the scope is destroyed after use.

This approach makes it easy to swap out implementations, manage complex lifecycles, and keep your codebase clean and maintainable.

## Code of Conduct

This project has adopted the [Contributor Covenant](https://www.contributor-covenant.org/) version 2.1 as our code of conduct. Please see the details in our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). All contributors must abide by the code of conduct.

## Working Language

The primary language for this project is **English**. All content will be available in English, and we ask that all communication, issues, and contributions be made in English to ensure consistency and accessibility.

## Support and Feedback

For discussions, feedback, or support, please use the following channels:

<!-- markdownlint-disable MD033 -->
| Type       | Channel                                                                                                                                                                       |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Issues** | <a href="/../../issues/new/choose" title="General Discussion"><img alt="General Discussion" src="https://img.shields.io/github/issues/lvlcn-t/meta?style=flat-square"></a> |
<!-- markdownlint-enable MD033 -->

## How to Contribute

Contribution and feedback is encouraged and always welcome. For more information about how to contribute, the project
structure, as well as additional contribution information, see our [Contribution Guidelines](./CONTRIBUTING.md). By
participating in this project, you agree to abide by its [Code of Conduct](./CODE_OF_CONDUCT.md) at all times.

## Licensing

Copyright (c) 2024 lvlcn-t.

Licensed under the **MIT** (the "License"); you may not use this file except in compliance with
the License.

You may obtain a copy of the License at <https://www.mit.edu/~amini/LICENSE.md>.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "
AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the [LICENSE](./LICENSE) for
the specific language governing permissions and limitations under the License.
