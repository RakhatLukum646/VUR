import asyncio
import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_ROOT))

from app.db import ensure_indexes


def main() -> None:
    asyncio.run(ensure_indexes())
    print("Auth service indexes are ready.")


if __name__ == "__main__":
    main()
