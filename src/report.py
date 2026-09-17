"""Command-line sales report.

Usage:
    python3 -m src.report                    # portfolio summary
    python3 -m src.report --by model         # break down by suite model
    python3 -m src.report --by agent         # sales leaderboard
    python3 -m src.report --by exposure      # exposure premium
    python3 -m src.report --project GG-02    # single project detail
"""
import argparse

from . import metrics
from .loader import load_projects, load_transactions, load_units


def money(value):
    return "${:,.0f}".format(value)


def print_table(rows, columns):
    """Print rows as a fixed-width table. columns is [(key, header, align)]."""
    if not rows:
        print("  (no rows)")
        return

    widths = []
    for key, header, _align in columns:
        longest = max(len(str(row[key])) for row in rows)
        widths.append(max(len(header), longest))

    header_line = "  ".join(
        header.ljust(width) if align == "l" else header.rjust(width)
        for (_key, header, align), width in zip(columns, widths)
    )
    print(header_line)
    print("  ".join("-" * width for width in widths))

    for row in rows:
        print("  ".join(
            str(row[key]).ljust(width) if align == "l" else str(row[key]).rjust(width)
            for (key, _header, align), width in zip(columns, widths)
        ))


def report_projects(projects, units, transactions):
    rows = metrics.project_rollup(projects, units, transactions)
    display = [{
        "project_id": r["project_id"],
        "project_name": r["project_name"],
        "neighbourhood": r["neighbourhood"],
        "launch": r["launch_date"],
        "tracked": r["units_tracked"],
        "sold": r["sold"],
        "avail": r["available"],
        "absorption": "{:.1f}%".format(r["absorption_pct"]),
        "list_ppsf": "${:,.0f}".format(r["avg_list_ppsf"]),
        "sold_ppsf": "${:,.0f}".format(r["avg_sold_ppsf"]),
        "revenue": money(r["revenue"]),
    } for r in rows]

    print("\nPORTFOLIO BY PROJECT")
    print_table(display, [
        ("project_id", "ID", "l"),
        ("project_name", "PROJECT", "l"),
        ("neighbourhood", "NEIGHBOURHOOD", "l"),
        ("launch", "LAUNCH", "l"),
        ("tracked", "UNITS", "r"),
        ("sold", "SOLD", "r"),
        ("avail", "AVAIL", "r"),
        ("absorption", "ABSORB", "r"),
        ("list_ppsf", "LIST/SF", "r"),
        ("sold_ppsf", "SOLD/SF", "r"),
        ("revenue", "REVENUE", "r"),
    ])

    total_revenue = sum(r["revenue"] for r in rows)
    print("\n  Portfolio revenue: {}".format(money(total_revenue)))
    print("  Portfolio absorption: {:.1f}%".format(metrics.absorption_rate(units)))


def report_models(units, transactions):
    rows = metrics.model_rollup(units, transactions)
    display = [{
        "model": r["model"],
        "beds": r["beds"],
        "units": r["units_tracked"],
        "avg_sqft": r["avg_sqft"],
        "avg_price": money(r["avg_list_price"]),
        "list_ppsf": "${:,.0f}".format(r["avg_list_ppsf"]),
        "sold_ppsf": "${:,.0f}".format(r["avg_sold_ppsf"]),
        "absorption": "{:.1f}%".format(r["absorption_pct"]),
    } for r in rows]

    print("\nBY SUITE MODEL")
    print_table(display, [
        ("model", "MODEL", "l"),
        ("beds", "BEDS", "r"),
        ("units", "UNITS", "r"),
        ("avg_sqft", "AVG SF", "r"),
        ("avg_price", "AVG LIST", "r"),
        ("list_ppsf", "LIST/SF", "r"),
        ("sold_ppsf", "SOLD/SF", "r"),
        ("absorption", "ABSORB", "r"),
    ])


def report_agents(transactions):
    rows = metrics.agent_rollup(transactions)
    display = [{
        "agent": r["agent"],
        "brokerage": r["brokerage"],
        "deals": r["deals"],
        "revenue": money(r["revenue"]),
        "discount": "{:.2f}%".format(r["avg_discount_pct"]),
    } for r in rows]

    print("\nSALES LEADERBOARD")
    print_table(display, [
        ("agent", "AGENT", "l"),
        ("brokerage", "BROKERAGE", "l"),
        ("deals", "DEALS", "r"),
        ("revenue", "REVENUE", "r"),
        ("discount", "AVG DISC", "r"),
    ])


def report_exposure(units):
    rows = metrics.exposure_premium(units)
    display = [{
        "exposure": r["exposure"],
        "units": r["units"],
        "list_ppsf": "${:,.0f}".format(r["avg_list_ppsf"]),
    } for r in rows]

    print("\nEXPOSURE PREMIUM")
    print_table(display, [
        ("exposure", "FACING", "l"),
        ("units", "UNITS", "r"),
        ("list_ppsf", "LIST/SF", "r"),
    ])


def report_single_project(project_id, projects, units, transactions):
    project = next((p for p in projects if p["project_id"] == project_id), None)
    if project is None:
        valid = ", ".join(p["project_id"] for p in projects)
        raise SystemExit("Unknown project '{}'. Try one of: {}".format(project_id, valid))

    p_units = [u for u in units if u["project_id"] == project_id]
    p_txns = [t for t in transactions if t["project_id"] == project_id]
    summary = metrics.project_rollup([project], p_units, p_txns)[0]

    print("\n{} -- {}".format(project["project_name"], project["project_id"]))
    print("{}, {}".format(project["neighbourhood"], project["municipality"]))
    print("{} storeys / {} total units / launched {} / occupancy {}".format(
        project["storeys"], project["total_units"],
        project["launch_date"], project["occupancy_target"],
    ))
    print("Absorption {:.1f}% on {} tracked units | revenue {} | avg {} days to firm".format(
        summary["absorption_pct"], summary["units_tracked"],
        money(summary["revenue"]), summary["avg_days_on_market"],
    ))

    display = [{
        "suite": u["suite"],
        "model": u["model"],
        "sqft": u["interior_sqft"],
        "exposure": u["exposure"],
        "list_price": money(u["list_price"]),
        "ppsf": "${:,.0f}".format(
            metrics.price_per_sqft(u["list_price"], u["interior_sqft"])
        ),
        "status": u["status"],
    } for u in sorted(p_units, key=lambda r: r["suite"])]

    print("")
    print_table(display, [
        ("suite", "SUITE", "l"),
        ("model", "MODEL", "l"),
        ("sqft", "SF", "r"),
        ("exposure", "FACE", "l"),
        ("list_price", "LIST", "r"),
        ("ppsf", "$/SF", "r"),
        ("status", "STATUS", "l"),
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Mock GTA high-rise sales reporting.",
    )
    parser.add_argument(
        "--by",
        choices=["project", "model", "agent", "exposure"],
        default="project",
        help="which breakdown to print (default: project)",
    )
    parser.add_argument(
        "--project",
        metavar="ID",
        help="show detail for a single project, e.g. GG-02",
    )
    args = parser.parse_args(argv)

    projects = load_projects()
    units = load_units()
    transactions = load_transactions()

    if args.project:
        report_single_project(args.project, projects, units, transactions)
    elif args.by == "model":
        report_models(units, transactions)
    elif args.by == "agent":
        report_agents(transactions)
    elif args.by == "exposure":
        report_exposure(units)
    else:
        report_projects(projects, units, transactions)

    print("")


if __name__ == "__main__":
    main()
