"""Sales metrics for pre-construction high-rise inventory.

Every function takes plain lists/dicts (as returned by loader.py) so the
maths stays easy to unit test.
"""
from collections import defaultdict
from datetime import date

from .loader import SOLD_STATUSES


def price_per_sqft(price, interior_sqft):
    """Dollars per interior square foot, rounded to the cent.

    Balcony space is deliberately excluded -- GTA pre-construction is
    priced on interior area.
    """
    if interior_sqft <= 0:
        raise ValueError("interior_sqft must be positive")
    return round(price / interior_sqft, 2)


def status_counts(units):
    """Count units by sales status."""
    counts = defaultdict(int)
    for unit in units:
        counts[unit["status"]] += 1
    return dict(counts)


def absorption_rate(units):
    """Share of tracked units that are firm or closed, as a percentage."""
    if not units:
        return 0.0
    sold = sum(1 for u in units if u["status"] in SOLD_STATUSES)
    return round(100.0 * sold / len(units), 1)


def discount_pct(list_price, sold_price):
    """How far below list a unit traded, as a percentage."""
    if list_price <= 0:
        raise ValueError("list_price must be positive")
    return round(100.0 * (list_price - sold_price) / list_price, 2)


def days_on_market(launch_date, sale_date):
    """Days between project launch and the firm sale."""
    launch = date.fromisoformat(launch_date)
    sale = date.fromisoformat(sale_date)
    return (sale - launch).days


def _mean(values):
    return round(sum(values) / len(values), 2) if values else 0.0


def project_rollup(projects, units, transactions):
    """One summary row per project, in launch-date order."""
    units_by_project = defaultdict(list)
    for unit in units:
        units_by_project[unit["project_id"]].append(unit)

    txns_by_project = defaultdict(list)
    for txn in transactions:
        txns_by_project[txn["project_id"]].append(txn)

    unit_lookup = {u["unit_id"]: u for u in units}

    rows = []
    for project in sorted(projects, key=lambda p: p["launch_date"]):
        pid = project["project_id"]
        p_units = units_by_project.get(pid, [])
        p_txns = txns_by_project.get(pid, [])
        counts = status_counts(p_units)

        sold_ppsf = []
        for txn in p_txns:
            unit = unit_lookup.get(txn["unit_id"])
            if unit:
                sold_ppsf.append(price_per_sqft(txn["sold_price"], unit["interior_sqft"]))

        rows.append({
            "project_id": pid,
            "project_name": project["project_name"],
            "municipality": project["municipality"],
            "neighbourhood": project["neighbourhood"],
            "launch_date": project["launch_date"],
            "units_tracked": len(p_units),
            "available": counts.get("available", 0),
            "held": counts.get("held", 0),
            "sold": counts.get("firm", 0) + counts.get("closed", 0),
            "absorption_pct": absorption_rate(p_units),
            "avg_list_ppsf": _mean([
                price_per_sqft(u["list_price"], u["interior_sqft"]) for u in p_units
            ]),
            "avg_sold_ppsf": _mean(sold_ppsf),
            "avg_discount_pct": _mean([
                discount_pct(t["list_price"], t["sold_price"]) for t in p_txns
            ]),
            "revenue": sum(t["sold_price"] for t in p_txns),
            "avg_days_on_market": _mean([
                days_on_market(project["launch_date"], t["sale_date"]) for t in p_txns
            ]),
        })
    return rows


def model_rollup(units, transactions):
    """Summary by suite model (Studio, 1B, 2B+D, ...), largest first."""
    unit_lookup = {u["unit_id"]: u for u in units}

    by_model = defaultdict(lambda: {"units": [], "sold_ppsf": []})
    for unit in units:
        by_model[unit["model"]]["units"].append(unit)
    for txn in transactions:
        unit = unit_lookup.get(txn["unit_id"])
        if unit:
            by_model[unit["model"]]["sold_ppsf"].append(
                price_per_sqft(txn["sold_price"], unit["interior_sqft"])
            )

    rows = []
    for model, bucket in by_model.items():
        m_units = bucket["units"]
        rows.append({
            "model": model,
            "beds": m_units[0]["beds"],
            "units_tracked": len(m_units),
            "avg_sqft": int(_mean([u["interior_sqft"] for u in m_units])),
            "avg_list_price": int(_mean([u["list_price"] for u in m_units])),
            "avg_list_ppsf": _mean([
                price_per_sqft(u["list_price"], u["interior_sqft"]) for u in m_units
            ]),
            "avg_sold_ppsf": _mean(bucket["sold_ppsf"]),
            "absorption_pct": absorption_rate(m_units),
        })
    return sorted(rows, key=lambda r: (r["beds"], r["avg_sqft"]))


def agent_rollup(transactions):
    """Sales leaderboard, best revenue first."""
    by_agent = defaultdict(list)
    for txn in transactions:
        by_agent[(txn["agent"], txn["brokerage"])].append(txn)

    rows = []
    for (agent, brokerage), txns in by_agent.items():
        rows.append({
            "agent": agent,
            "brokerage": brokerage,
            "deals": len(txns),
            "revenue": sum(t["sold_price"] for t in txns),
            "avg_discount_pct": _mean([
                discount_pct(t["list_price"], t["sold_price"]) for t in txns
            ]),
        })
    return sorted(rows, key=lambda r: r["revenue"], reverse=True)


def exposure_premium(units):
    """Average list $/sqft by exposure -- shows the south-facing premium."""
    by_exposure = defaultdict(list)
    for unit in units:
        by_exposure[unit["exposure"]].append(
            price_per_sqft(unit["list_price"], unit["interior_sqft"])
        )
    rows = [
        {"exposure": exposure, "units": len(ppsf), "avg_list_ppsf": _mean(ppsf)}
        for exposure, ppsf in by_exposure.items()
    ]
    return sorted(rows, key=lambda r: r["avg_list_ppsf"], reverse=True)
