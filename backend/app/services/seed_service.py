"""Seed service for demo database bootstrap.

Loads sample customers, subscriptions, workspaces, products, support articles,
incidents, and scenario tickets (CD-1001 through CD-1013) on startup.
"""

from collections.abc import AsyncGenerator
import json
import logging
from pathlib import Path
import re
from typing import Any
import yaml

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.database import db_session
from backend.app.models.entities import (
    Customer,
    CustomerMemory,
    Incident,
    Product,
    Profile,
    Subscription,
    SupportArticle,
    Ticket,
    TicketMessage,
    Workspace,
)
from backend.app.schemas.common import UserRole

logger = logging.getLogger(__name__)


def get_sample_data_dir() -> Path:
    """Resolve the path to the sample_data directory."""
    settings = get_settings()
    configured_dir = Path(settings.SAMPLE_DATA_DIR)
    if configured_dir.is_dir():
        return configured_dir.resolve()

    # Search upwards from current file location
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        candidate = parent / "sample_data"
        if candidate.is_dir():
            return candidate

    return Path("sample_data").resolve()


def load_knowledge_articles(kb_dir: Path) -> list[dict[str, Any]]:
    """Parse Markdown knowledge base articles with YAML front-matter."""
    articles: list[dict[str, Any]] = []
    if not kb_dir.is_dir():
        return articles

    front_matter_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

    for md_file in sorted(kb_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        match = front_matter_pattern.match(text)
        if match:
            fm_str, content = match.group(1), match.group(2).strip()
            meta = yaml.safe_load(fm_str) or {}
            articles.append(
                {
                    "slug": md_file.stem,
                    "title": meta.get("title", md_file.stem.replace("-", " ").title()),
                    "category": meta.get("category", "other"),
                    "tags": meta.get("tags", []),
                    "summary": meta.get("summary", ""),
                    "content": content,
                }
            )
        else:
            articles.append(
                {
                    "slug": md_file.stem,
                    "title": md_file.stem.replace("-", " ").title(),
                    "category": "other",
                    "tags": [],
                    "summary": "",
                    "content": text.strip(),
                }
            )

    return articles


async def _execute_stmt(session: AsyncSession | Session, stmt: Any) -> Any:
    """Execute statement on either async or synchronous session."""
    if isinstance(session, AsyncSession):
        return await session.execute(stmt)
    return session.execute(stmt)


async def _commit_session(session: AsyncSession | Session) -> None:
    """Commit transaction on either async or synchronous session."""
    if isinstance(session, AsyncSession):
        await session.commit()
    else:
        session.commit()


async def _flush_session(session: AsyncSession | Session) -> None:
    """Flush pending changes on either async or synchronous session."""
    if isinstance(session, AsyncSession):
        await session.flush()
    else:
        session.flush()


async def bootstrap_demo_data(
    session: AsyncSession | Session | None = None,
    force: bool = False,
) -> dict[str, int]:
    """Bootstrap demo database with profiles, customers, products, tickets, and KB articles.

    Idempotent: If tickets already exist and force=False, returns immediately without modifying.
    """
    if session is None:
        async with db_session() as s:
            return await _bootstrap_internal(s, force=force)
    return await _bootstrap_internal(session, force=force)


async def _bootstrap_internal(
    session: AsyncSession | Session, force: bool = False
) -> dict[str, int]:
    data_dir = get_sample_data_dir()
    stats = {
        "profiles": 0,
        "products": 0,
        "customers": 0,
        "subscriptions": 0,
        "workspaces": 0,
        "incidents": 0,
        "articles": 0,
        "tickets": 0,
        "messages": 0,
    }

    # Check existing tickets
    t_count_stmt = select(func.count(Ticket.id))
    t_count_res = await _execute_stmt(session, t_count_stmt)
    existing_tickets = int(t_count_res.scalar_one() or 0)

    if existing_tickets > 0 and not force:
        logger.info(
            "Demo database already contains %d tickets. Skipping bootstrap.",
            existing_tickets,
        )
        return stats

    # 1. Demo Staff Profiles
    demo_profiles = [
        Profile(
            email="admin@clouddesk.demo",
            full_name="Admin User",
            role=UserRole.ADMIN.value,
            avatar_url="https://avatar.vercel.sh/admin",
        ),
        Profile(
            email="sam.agent@clouddesk.demo",
            full_name="Sam Agent",
            role=UserRole.AGENT.value,
            avatar_url="https://avatar.vercel.sh/sam",
        ),
        Profile(
            email="vic.viewer@clouddesk.demo",
            full_name="Vic Viewer",
            role=UserRole.VIEWER.value,
            avatar_url="https://avatar.vercel.sh/vic",
        ),
    ]
    for p in demo_profiles:
        exists_stmt = select(Profile).where(Profile.email == p.email)
        exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
        if not exists:
            session.add(p)
            stats["profiles"] += 1

    await _flush_session(session)

    # 2. Products
    products_file = data_dir / "products.json"
    if products_file.is_file():
        prod_data = json.loads(products_file.read_text(encoding="utf-8"))
        for item in prod_data:
            exists_stmt = select(Product).where(Product.code == item["code"])
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                session.add(
                    Product(
                        id=item.get("id"),
                        name=item["name"],
                        code=item["code"],
                        tier=item.get("tier", "free"),
                        base_price=item.get("base_price", 0.0),
                        description=item.get("description"),
                    )
                )
                stats["products"] += 1

    await _flush_session(session)

    # 3. Customers
    cust_id_map: dict[str, str] = {}
    customers_file = data_dir / "customers.json"
    if customers_file.is_file():
        cust_data = json.loads(customers_file.read_text(encoding="utf-8"))
        for item in cust_data:
            exists_stmt = select(Customer).where(Customer.email == item["email"])
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                cust = Customer(
                    id=item.get("id"),
                    name=item["name"],
                    email=item["email"],
                    company=item["company"],
                    plan_name=item.get("plan_name", "free"),
                    status=item.get("status", "active"),
                    region=item.get("region", "us-east"),
                    lifetime_value=item.get("lifetime_value", 0.0),
                )
                session.add(cust)
                stats["customers"] += 1
                cust_id_map[item["id"]] = cust.id
            else:
                cust_id_map[item["id"]] = exists.id

    await _flush_session(session)

    # 4. Subscriptions
    subs_file = data_dir / "subscriptions.json"
    if subs_file.is_file():
        subs_data = json.loads(subs_file.read_text(encoding="utf-8"))
        for item in subs_data:
            cust_id = cust_id_map.get(item["customer_id"], item["customer_id"])
            exists_stmt = select(Subscription).where(
                Subscription.customer_id == cust_id
            )
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                session.add(
                    Subscription(
                        id=item.get("id"),
                        customer_id=cust_id,
                        plan=item.get("plan", "free"),
                        seats=item.get("seats", 1),
                        status=item.get("status", "active"),
                        mrr=item.get("mrr", 0.0),
                        storage_quota_gb=item.get("storage_quota_gb", 10),
                        storage_used_gb=item.get("storage_used_gb", 0.0),
                        api_rate_limit=item.get("api_rate_limit", 120),
                    )
                )
                stats["subscriptions"] += 1

    # 5. Workspaces
    ws_file = data_dir / "workspaces.json"
    if ws_file.is_file():
        ws_data = json.loads(ws_file.read_text(encoding="utf-8"))
        for item in ws_data:
            cust_id = cust_id_map.get(item["customer_id"], item["customer_id"])
            exists_stmt = select(Workspace).where(
                Workspace.customer_id == cust_id, Workspace.name == item["name"]
            )
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                session.add(
                    Workspace(
                        id=item.get("id"),
                        customer_id=cust_id,
                        name=item["name"],
                        member_count=item.get("member_count", 1),
                        storage_used_gb=item.get("storage_used_gb", 0.0),
                        integrations=item.get("integrations", []),
                        sso_enabled=item.get("sso_enabled", False),
                    )
                )
                stats["workspaces"] += 1

    # 6. Incidents
    inc_file = data_dir / "incidents.json"
    if inc_file.is_file():
        inc_data = json.loads(inc_file.read_text(encoding="utf-8"))
        for item in inc_data:
            exists_stmt = select(Incident).where(Incident.title == item["title"])
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                session.add(
                    Incident(
                        id=item.get("id"),
                        title=item["title"],
                        description=item["description"],
                        status=item.get("status", "investigating"),
                        severity=item.get("severity", "medium"),
                        affected_services=item.get("affected_services", []),
                    )
                )
                stats["incidents"] += 1

    # 7. Knowledge Base Articles
    kb_dir = data_dir / "knowledge_base"
    articles = load_knowledge_articles(kb_dir)
    for art in articles:
        exists_stmt = select(SupportArticle).where(SupportArticle.slug == art["slug"])
        exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
        if not exists:
            session.add(
                SupportArticle(
                    slug=art["slug"],
                    title=art["title"],
                    category=art["category"],
                    tags=art["tags"],
                    summary=art["summary"],
                    content=art["content"],
                )
            )
            stats["articles"] += 1

    await _flush_session(session)

    # 8. Tickets and Initial Messages
    tickets_file = data_dir / "tickets.json"
    if tickets_file.is_file():
        tkt_data = json.loads(tickets_file.read_text(encoding="utf-8"))
        for item in tkt_data:
            exists_stmt = select(Ticket).where(
                Ticket.ticket_number == item["ticket_number"]
            )
            exists = (await _execute_stmt(session, exists_stmt)).scalars().first()
            if not exists:
                resolved_cust_id = cust_id_map.get(
                    item["customer_id"], item["customer_id"]
                )
                ticket = Ticket(
                    id=item.get("id"),
                    ticket_number=item["ticket_number"],
                    subject=item["subject"],
                    body=item["body"],
                    category=item.get("category", "other"),
                    severity=item.get("severity", "low"),
                    status=item.get("status", "new"),
                    customer_id=resolved_cust_id,
                    channel=item.get("channel", "email"),
                    tags=item.get("tags", []),
                    escalation_required=item.get("escalation_required", False),
                    approval_status=item.get("approval_status", "not_required"),
                )
                session.add(ticket)
                stats["tickets"] += 1

                # Create initial customer message in thread
                msg = TicketMessage(
                    ticket_id=ticket.id,
                    author_name="Customer Contact",
                    body=ticket.body,
                    role="customer",
                    internal=False,
                )
                session.add(msg)
                stats["messages"] += 1

    await _commit_session(session)
    logger.info("Successfully bootstrapped demo database: %s", stats)
    return stats

