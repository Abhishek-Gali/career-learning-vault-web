# Python Coding Standards

- **Type Annotations**: Mandatory on all function arguments, return types, and class attributes.
- **Pydantic v2**: Use `BaseModel` for schemas; use `model_dump()`, `model_dump_json()`, `model_validate()` (no deprecated v1 methods).
- **Settings**: Use `pydantic_settings.BaseSettings` for configuration models.
- **Logging**: Use `app.core.logging.get_logger(__name__)`. Never use raw `print()` statements in application modules.
- **Exceptions**: Raise structured custom exceptions inheriting from `CLFResearcherError` in `app.core.exceptions`.
- **Formatting**: Adhere to PEP 8, 100 character line length.
