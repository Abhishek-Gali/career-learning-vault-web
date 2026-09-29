# Architecture Rules

- **Layered Flow**: Discovery -> Fetching -> Extraction -> Processing -> Storage -> Presentation.
- **No Circular Imports**: Lower layers must never import higher layers (e.g., `app.core` must never import `app.web`).
- **Path Isolation**: All filesystem access must be computed through `app.core.paths` constants. Never hardcode absolute path strings.
- **Stateless Services**: Pipeline processing stages must remain stateless functions or dependency-injected classes.
- **Async First**: Use `async`/`await` for all network I/O, database access, and background jobs. Offload CPU-bound HTML/PDF parsing to `asyncio.to_thread`.
