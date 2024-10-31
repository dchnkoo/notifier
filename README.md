# Notification framework

[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](

## Overview

This project provides a framework for creating and managing notifications. It includes classes and functions to define events, messages, and notifiers, and to handle the sending of notifications.

## Modules

### `__init__.py`

This module contains the main classes and functions for the notification framework.

#### Classes

- **Event**: An enumeration of possible event types.
- **Message**: A class representing a message with an event, text, and additional metadata.
- **Notifier**: An abstract base class for notifiers that send messages.
- **Notifiers**: A class that manages multiple notifiers and sends messages to all of them.

#### Functions

- **is_message(obj)**: Checks if an object is an instance of the `Message` class.
- **is_notifier(obj)**: Checks if an object is an instance of the `Notifier` class.
- **message(text, \*, event=Event.INFO, \*\*kwargs)**: Creates a `Message` instance and returns a sender object to send the message to notifiers.

#### Usage

1. **Define a Notifier**: Create a subclass of `Notifier` and implement the `notify` method.
2. **Create a Message**: Use the `message` function to create a `Message` instance.
3. **Send the Message**: Use the sender object returned by the `message` function to send the message to one or more notifiers.

Example:
```python
class PrintNotifier(Notifier):
    def notify(self, msg: Message) -> None:
        print(f"{msg.event}: {msg.text}")

msg = message("This is a test message", event=Event.INFO)
notifier = PrintNotifier()
msg.to(notifier).send()
```

Example 2:
```python
class AsyncNotifier(Notifier):
    async def notify(self, msg: Message) -> None:
        await asyncio.sleep(1)  # Simulate async operation
        print(f"Async {msg.event}: {msg.text}")

class PrintNotifier(Notifier):
    def notify(self, msg: Message) -> None:
        print(f"{msg.event}: {msg.text}")

async def main():
    msg = message("This is a test message for multiple notifiers")

    notifier = PrintNotifier()
    async_notifier = AsyncNotifier()

    msg.to([notifier, async_notifier]).send()
```
Example 3:
```python
class PrintNotifier(Notifier):
    def notify(self, msg: Message) -> None:
        print(f"{msg.event}: {msg.text}")
        print(f"Data: {msg.kwargs}")

class AsyncNotifier(Notifier):
    async def notify(self, msg: Message) -> None:
        await asyncio.sleep(1)  # Simulate async operation
        print(f"Async {msg.event}: {msg.text}")

class MyNotifiers(Notifiers):
    print_notifier = PrintNotifier()
    async_notifier = AsyncNotifier()

async def main():
    msg = Message(Event.SUCCESS, "This is a test message for all notifiers", some_data={"key": "value"})
    notifiers = MyNotifiers()
    notifiers.to_all(msg).send()

asyncio.run(main())
```

### How to Use the `notify` Decorator

The `notify` decorator is used to wrap generator functions (both synchronous and asynchronous) to automatically send messages to notifiers. Here is how you can use it:

1. **Define Notifiers**: Create subclasses of `Notifier` and implement the `notify` method.
2. **Create a Notifiers Manager**: Create a class that inherits from `Notifiers` and define your notifiers as class attributes.
3. **Decorate Generator Functions**: Use the `notify` decorator on your generator functions.

### Examples with `notify` Decorator

Example 1:
```python
class PrintNotifier(Notifier):
    def notify(self, msg: Message) -> None:
        print(f"{msg.event}: {msg.text}")

class MyNotifiers(Notifiers):
    print_notifier = PrintNotifier()

@notify(MyNotifiers())
def my_generator():
    yield Message(Event.INFO, "This is a test message")

my_generator()
```

To use the `notify` decorator with the `return_values` argument, follow these steps:

1. **Define Notifiers**: Create subclasses of `Notifier` and implement the `notify` method.
2. **Create a Notifiers Manager**: Create a class that inherits from `Notifiers` and define your notifiers as class attributes.
3. **Decorate Generator Functions**: Use the `notify` decorator on your generator functions, and set the `return_values` argument to `True`.

### Example 1: Synchronous Generator with `return_values=True`
```python
class PrintNotifier(Notifier):
    def notify(self, msg: Message) -> None:
        print(f"{msg.event}: {msg.text}")

class MyNotifiers(Notifiers):
    print_notifier = PrintNotifier()

@notify(MyNotifiers(), return_values=True)
def my_generator():
    yield Message(Event.INFO, "This is a test message")
    yield "This is a return value"

for value in my_generator():
    print(f"Returned value: {value}")
```

### Example 2: Asynchronous Generator with `return_values=True`
```python
class AsyncNotifier(Notifier):
    async def notify(self, msg: Message) -> None:
        await asyncio.sleep(1)  # Simulate async operation
        print(f"Async {msg.event}: {msg.text}")

class MyNotifiers(Notifiers):
    async_notifier = AsyncNotifier()

@notify(MyNotifiers(), return_values=True)
async def my_async_generator():
    yield Message(Event.INFO, "This is a test message")
    yield "This is a return value"

async def main():
    async for value in my_async_generator():
        print(f"Returned value: {value}")

asyncio.run(main())
```

### What the Generators Return

- **Synchronous Generator**: The generator will not yield  `Message` instances, only other values! In the example, it will print:
  ```
  Returned value: This is a return value
  ```

- **Asynchronous Generator**: Similarly. In the example, it will print:
  ```
  Returned value: This is a return value
  ```