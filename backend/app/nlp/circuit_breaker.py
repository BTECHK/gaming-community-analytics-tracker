"""Circuit breaker pattern for NLP model protection."""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation, requests flow through
    OPEN = "open"  # Failing, requests are rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker to protect against cascading failures.

    States:
    - CLOSED: Normal operation. Track failures, open circuit if threshold exceeded.
    - OPEN: Service is failing. Reject requests immediately. After cooldown, move to HALF_OPEN.
    - HALF_OPEN: Allow one test request. If success, close circuit. If failure, open again.

    Usage:
        breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)

        try:
            result = breaker.call(some_function, arg1, arg2)
        except CircuitOpenError:
            # Handle circuit open (service unavailable)
            pass
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 60.0,
        name: str = "default",
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit.
            cooldown_seconds: Seconds to wait before testing recovery.
            name: Identifier for logging.
        """
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed through."""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if cooldown period has passed
            if self._last_failure_time is None:
                return True

            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "Circuit breaker '%s' entering half-open state",
                    self.name,
                )
                return True
            return False

        # HALF_OPEN: allow one test request
        return True

    def _record_success(self) -> None:
        """Record a successful request."""
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            logger.info("Circuit breaker '%s' closed after successful recovery", self.name)
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self, error: Exception) -> None:
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Failed during recovery test, reopen circuit
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker '%s' reopened after failed recovery test: %s",
                self.name,
                error,
            )
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker '%s' opened after %d failures: %s",
                    self.name,
                    self._failure_count,
                    error,
                )

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function through circuit breaker.

        Args:
            func: Function to call.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result from function.

        Raises:
            CircuitOpenError: If circuit is open.
            Exception: Any exception from the function.
        """
        if not self._should_allow_request():
            raise CircuitOpenError(
                f"Circuit breaker '{self.name}' is open. Service unavailable."
            )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    async def call_async(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute async function through circuit breaker.

        Args:
            func: Async function to call.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result from function.

        Raises:
            CircuitOpenError: If circuit is open.
            Exception: Any exception from the function.
        """
        async with self._lock:
            if not self._should_allow_request():
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is open. Service unavailable."
                )

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._record_success()
            return result
        except Exception as e:
            async with self._lock:
                self._record_failure(e)
            raise

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        logger.info("Circuit breaker '%s' manually reset", self.name)

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status.

        Returns:
            Dict with state information.
        """
        cooldown_remaining = None
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            cooldown_remaining = max(0, self.cooldown_seconds - elapsed)

        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "cooldown_remaining": cooldown_remaining,
        }


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open."""

    pass


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for retry with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap.
        exponential_base: Multiplier for exponential growth.
        retryable_exceptions: Exception types to retry on.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(
                            base_delay * (exponential_base**attempt),
                            max_delay,
                        )
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            delay,
                            e,
                        )
                        time.sleep(delay)
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def with_retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
) -> Callable:
    """Async decorator for retry with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap.
        exponential_base: Multiplier for exponential growth.
        retryable_exceptions: Exception types to retry on.

    Returns:
        Decorated async function.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(
                            base_delay * (exponential_base**attempt),
                            max_delay,
                        )
                        logger.warning(
                            "Retry %d/%d for %s after %.1fs: %s",
                            attempt + 1,
                            max_attempts,
                            func.__name__,
                            delay,
                            e,
                        )
                        await asyncio.sleep(delay)
            raise last_exception  # type: ignore

        return wrapper

    return decorator


# Global circuit breakers for NLP models
_model_breakers: dict[str, CircuitBreaker] = {}


def get_model_breaker(model_name: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a model.

    Args:
        model_name: Model identifier.

    Returns:
        CircuitBreaker instance.
    """
    if model_name not in _model_breakers:
        _model_breakers[model_name] = CircuitBreaker(
            failure_threshold=3,
            cooldown_seconds=120.0,
            name=f"model:{model_name}",
        )
    return _model_breakers[model_name]


def get_all_breaker_statuses() -> list[dict[str, Any]]:
    """Get status of all circuit breakers.

    Returns:
        List of breaker status dicts.
    """
    return [breaker.get_status() for breaker in _model_breakers.values()]
