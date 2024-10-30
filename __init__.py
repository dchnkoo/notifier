from collections.abc import Iterable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
from enum import StrEnum
from pathlib import Path

import  typing as _t
import inspect
import asyncio
import  types


__all__ = (
    "Event",
    "Message",
    "Notifier",
    "is_message",
    "is_notifier",
    "message",
    "Notifiers",
)


class Event(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SUCCESS = "success"
    FAILURE = "failure"
    EXCEPTION = "exception"
    DEBUG = "debug"


@dataclass
class Message:
    event: Event
    text: str

    def __init__(self, event: Event, text: str, **kwargs):
        assert event in Event, f"Expected Event, got {event}"
        assert isinstance(text, str), f"Expected str, got {type(text)}"

        self.event = event
        self.text = text
        self.kwargs = kwargs

    @property
    def timestamp(self):
        return datetime.now()

    @property
    def date(self):
        return self.timestamp.strftime("%Y-%m-%d")

    @property
    def time(self):
        return self.timestamp.strftime("%H:%M:%S")

    @property
    def module(self):
        return Path(inspect.stack()[-1].filename).resolve()


class Notifier(ABC):

    def __init__(self, *not_send_on: Event):
        self.not_send_on = not_send_on

    @abstractmethod
    def notify(self, msg: Message) -> None:
        pass


def is_(obj: _t.Any, cls: _t.Type[_t.Any]) -> bool:
    try:
        return isinstance(obj, cls) or issubclass(obj, cls)
    except TypeError:
        return False


def is_message(obj: _t.Any) -> bool:
    return is_(obj, Message)


def is_notifier(obj: _t.Any) -> bool:
    return is_(obj, Notifier)


def is_iterable(obj: _t.Any) -> bool:
    return is_(obj, Iterable)


def log_msg(notifier: type[Notifier], msg: Message):
    getattr(logger, msg.event)(notifier.__class__.__name__ + ": " + msg.text)


def get_event_loop():
    try:
        asyncio.get_running_loop()
        return  True
    except RuntimeError:
        return False


class _handle_notify[F]:

    def __init__(self, msg: Message, notifier: F):
        self._func = notifier.notify
        self._coro = inspect.iscoroutinefunction(self._func)
        self._notifier = notifier
        self._loop = get_event_loop()
        self._msg = msg

    def send(self):
        f = self._func
        log_msg(self._notifier, self._msg)
        if callable(f):
            try:
                if self._coro:
                    if self._loop:
                        asyncio.gather(f(self._msg))
                    else:
                        raise RuntimeError("Cannot run coroutine function outside of an event loop.")
                else:
                    f(self._msg)
            except Exception as e:
                logger.exception(e)
                return

class _handle_notify_many:

    def __init__(self, funcs: _t.Iterable[_handle_notify]):
        self._funcs = funcs

    def send(self):
        for func in self._funcs:
            func.send()


class _sender:

    def __init__(self, msg: Message):
        self.message = msg

    def to(self, notifier: Notifier | _t.Iterable[Notifier]):
        if is_iterable(notifier):
            return self.to_many(notifier)

        return self.to_one(notifier)

    def to_one(self, notifier: Notifier) -> _handle_notify:
        if self.message.event in notifier.not_send_on:
            raise ValueError(f"Message event {self.message.event.name} is not allowed to be sent by {notifier}.")
        return _handle_notify(self.message, notifier)

    def to_many(self, notifiers: _t.Iterable[Notifier]):
        n = []
        for notifier in notifiers:
            try:
                n.append(self.to_one(notifier))
            except ValueError:
                continue
        return _handle_notify_many(n)


def message(text: str, *, event: Event = Event.INFO, **kwargs):
    msg = Message(event, text, **kwargs)
    return _sender(msg)


class Notifiers:

    def __new__(cls, *args, **kwargs):
        if cls is Notifiers:
            raise TypeError("Cannot create instance of Notifiers class")

        instance = super().__new__(cls, *args, **kwargs)
        instance.message = message
        return instance

    def __init_subclass__(cls, **kwargs):
        notifiers = {name: obj for name, obj in cls.__dict__.items() if is_notifier(obj)}
        cls._notifiers = types.MappingProxyType(notifiers)

    def to_all(self, msg: Message):
        notifiers = self._notifiers.values()
        return _handle_notify_many([_handle_notify(msg, notifier) for notifier in notifiers])
