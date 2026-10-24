
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from langgraph.checkpoint.sqlite import SqliteSaver


@contextmanager
def sqlite_checkpointer(
    database_path: str | Path,
) -> Iterator[SqliteSaver]:
    """Manage a durable SQLite LangGraph checkpointer."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with SqliteSaver.from_conn_string(str(path)) as saver:
        yield saver