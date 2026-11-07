"""CLI script to seed the database with demo scenarios.

Invoked via `make seed` or `python -m backend.app.seed`.
"""

import asyncio
import sys

from backend.app.core.database import create_tables, db_session
from backend.app.core.logging import setup_logging
from backend.app.services.seed_service import bootstrap_demo_data


async def main() -> None:
    """Run database table creation and demo data seeding."""
    setup_logging()
    print("Ensuring database tables exist...")
    await create_tables()

    print("Bootstrapping sample demo data...")
    async with db_session() as session:
        stats = await bootstrap_demo_data(session=session, force=False)

    print(f"Seed complete. Loaded: {stats}")


if __name__ == "__main__":
    asyncio.run(main())

