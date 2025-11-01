from functools import wraps
from typing import Callable, Literal, get_args


def validate_literal_parameters(func: Callable) -> Callable:
    """
    Декоратор, который автоматически извлекает допустимые значения
    из аннотаций типа Literal и проверяет их
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        import inspect
        sig = inspect.signature(func)

        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        for param_name, param in sig.parameters.items():
            if param_name in bound_args.arguments:
                annotation = param.annotation
                # Проверяем, является ли аннотация Literal
                if hasattr(annotation, '__origin__') and annotation.__origin__ is Literal:
                    allowed_values = get_args(annotation)
                    value = bound_args.arguments[param_name]
                    if value not in allowed_values:
                        raise ValueError(f"{param_name} must be one of {allowed_values}, got '{value}'")

        return func(*args, **kwargs)

    return wrapper