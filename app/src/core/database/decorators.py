import functools
import inspect
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.transaction import Transaction, in_transaction

logger = logging.getLogger(__name__)

T = TypeVar("T")


def transactional(
    func: Callable[..., T],
) -> Callable[..., T | Coroutine[Any, Any, T]]:
    """
    Decorator for executing a function within a transaction.

    If the function execution succeeds, the transaction is committed (if outermost).
    If an exception is raised, the transaction is rolled back (if outermost).

    The function being decorated must have a session parameter or be a method
    of a class with a self.session attribute.

    Usage:
        @transactional
        async def my_function(session: AsyncSession, ...):
            # Function code here

        OR

        class MyService:
            def __init__(self, session: AsyncSession):
                self.session = session

            @transactional
            async def my_method(self, ...):
                # Method code here
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        session = None

        if args and hasattr(args[0], "session"):
            session = args[0].session
        elif "session" in kwargs:
            session = kwargs["session"]
        else:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            try:
                session_idx = param_names.index("session")
                if len(args) > session_idx:
                    session = args[session_idx]
                else:
                    raise ValueError("Session argument is required but not provided")
            except ValueError:
                raise ValueError("Could not find session parameter in function or method")

        if not isinstance(session, AsyncSession):
            raise TypeError("Session must be an instance of AsyncSession")

        # NOTE: If we're already in a transaction, just call the function
        if in_transaction():
            result = func(*args, **kwargs)
            return await result if inspect.iscoroutine(result) else result

        # Otherwise, start a new transaction
        async with Transaction(session):
            result = func(*args, **kwargs)
            return await result if inspect.iscoroutine(result) else result

    return wrapper
