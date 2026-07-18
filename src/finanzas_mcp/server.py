"""Punto de entrada del servidor finanzas-mcp (stdio)."""

from . import tools_operaciones, tools_ratios, tools_tributario, tools_valoracion  # noqa: F401  (registran tools)
from .app import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
