"""Generate a static HTML dashboard from the data in data/.

Reuses loader.py and metrics.py so the website and the command-line report
are always computed from the same source figures.

Usage:
    python3 -m src.build_site              # writes ./site
    python3 -m src.build_site --out _build # writes elsewhere

Standard library only, in keeping with the rest of the repo. Output is
generated -- never commit it, and never write it back into data/.
"""
import argparse
import html
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import metrics
from .loader import SOLD_STATUSES, load_projects, load_transactions, load_units

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "site"


# --------------------------------------------------------------------------
# formatting helpers
# --------------------------------------------------------------------------

def money(value):
    return "${:,.0f}".format(value)


def compact_money(value):
    """Short form for large standalone figures: $25.9M, $412K."""
    if abs(value) >= 1_000_000:
        return "${:.1f}M".format(value / 1_000_000)
    if abs(value) >= 1_000:
        return "${:.0f}K".format(value / 1_000)
    return money(value)


def pct(value):
    return "{:.1f}%".format(value)


def esc(value):
    return html.escape(str(value), quote=True)


# --------------------------------------------------------------------------
# dashboard figures
# --------------------------------------------------------------------------

def dashboard_absorption(units):
    """Absorption shown on the dashboard tiles."""
    sellable = [u for u in units if u["status"] != "held"]
    if not sellable:
        return 0.0
    sold = sum(1 for u in sellable if u["status"] in SOLD_STATUSES)
    return round(100.0 * sold / len(sellable), 1)


def detail_ppsf(unit):
    """Per-suite $/sqft used on the project detail pages."""
    return metrics.price_per_sqft(
        unit["list_price"], unit["interior_sqft"] + unit["balcony_sqft"]
    )


# --------------------------------------------------------------------------
# HTML primitives
# --------------------------------------------------------------------------

def table(rows, columns, caption=None):
    """columns is [(key, header, align)] -- align 'l' or 'r'."""
    if not rows:
        return '<p class="empty">No rows.</p>'

    out = ['<div class="table-wrap"><table>']
    if caption:
        out.append("<caption>{}</caption>".format(esc(caption)))
    out.append("<thead><tr>")
    for _key, header, align in columns:
        cls = ' class="num"' if align == "r" else ""
        out.append("<th{}>{}</th>".format(cls, esc(header)))
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        for key, _header, align in columns:
            cls = ' class="num"' if align == "r" else ""
            out.append("<td{}>{}</td>".format(cls, row[key]))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def stat_tile(label, value, note=None):
    note_html = '<div class="tile-note">{}</div>'.format(esc(note)) if note else ""
    return (
        '<div class="tile"><div class="tile-label">{}</div>'
        '<div class="tile-value">{}</div>{}</div>'
    ).format(esc(label), esc(value), note_html)


def absorption_chart(rows):
    """Single-series horizontal bar chart: absorption by project.

    One series, so no legend -- the heading names what is plotted. The table
    below the chart is the accessible view of the same numbers.
    """
    bars = []
    for row in rows:
        value = row["absorption_pct"]
        bar = (
            '<div class="bar-row" data-tip="{name} &middot; {sold} of {tracked} '
            'tracked suites sold">'
            '<div class="bar-label">{label}</div>'
            '<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%">'
            "</div></div>"
            '<div class="bar-value">{value}</div>'
            "</div>"
        ).format(
            name=esc(row["project_name"]),
            sold=row["sold"],
            tracked=row["units_tracked"],
            label=esc(row["project_id"]),
            width=max(value, 0.6),
            value=pct(value),
        )
        bars.append(bar)

    return (
        '<div class="chart">'
        '<div class="chart-scale"><span>0%</span><span>50%</span><span>100%</span></div>'
        "{}</div>"
    ).format("".join(bars))


# --------------------------------------------------------------------------
# page shell
# --------------------------------------------------------------------------

def page(title, body, subtitle=None, breadcrumb=None):
    crumb = breadcrumb or '<a href="index.html">&larr; Portfolio</a>'
    sub = '<p class="subtitle">{}</p>'.format(esc(subtitle)) if subtitle else ""
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; Sales Testing Environment</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="banner">Synthetic practice data &mdash; every project, suite, price
and agent below is invented. Nothing here is real.</div>
<header>
  <nav>{crumb}</nav>
  <button id="theme" type="button" aria-label="Toggle dark mode">Theme</button>
</header>
<main>
  <h1>{title}</h1>
  {sub}
  {body}
</main>
<footer>
  <p>Generated {built} by <code>python3 -m src.build_site</code>.</p>
</footer>
<div id="tip" role="tooltip" aria-hidden="true"></div>
<script src="app.js"></script>
</body>
</html>
""".format(title=esc(title), crumb=crumb, sub=sub, body=body, built=built)


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

def build_index(projects, units, transactions):
    rollup = metrics.project_rollup(projects, units, transactions)
    total_revenue = sum(r["revenue"] for r in rollup)
    sold_units = sum(1 for u in units if u["status"] in SOLD_STATUSES)

    tiles = "".join([
        stat_tile("Portfolio revenue", compact_money(total_revenue),
                  "{} firm or closed deals".format(len(transactions))),
        stat_tile("Absorption", pct(dashboard_absorption(units)),
                  "{} of {} tracked suites".format(sold_units, len(units))),
        stat_tile("Active projects", str(len(projects)),
                  "across 4 municipalities"),
        stat_tile("Suites tracked", str(len(units)),
                  "a sample, not the full towers"),
    ])

    project_rows = [{
        "project": '<a href="project-{pid}.html">{name}</a>'.format(
            pid=esc(r["project_id"]), name=esc(r["project_name"])),
        "neighbourhood": esc(r["neighbourhood"]),
        "launch": esc(r["launch_date"]),
        "tracked": r["units_tracked"],
        "sold": r["sold"],
        "available": r["available"],
        "absorption": pct(r["absorption_pct"]),
        "list_ppsf": money(r["avg_list_ppsf"]),
        "sold_ppsf": money(r["avg_sold_ppsf"]),
        "revenue": money(r["revenue"]),
    } for r in rollup]

    model_rows = [{
        "model": esc(r["model"]),
        "units": r["units_tracked"],
        "avg_sqft": "{:,}".format(r["avg_sqft"]),
        "avg_list": money(r["avg_list_price"]),
        "list_ppsf": money(r["avg_list_ppsf"]),
        "sold_ppsf": money(r["avg_sold_ppsf"]),
        "absorption": pct(r["absorption_pct"]),
    } for r in metrics.model_rollup(units, transactions)]

    agent_rows = [{
        "agent": esc(r["agent"]),
        "brokerage": esc(r["brokerage"]),
        "deals": r["deals"],
        "revenue": money(r["revenue"]),
        "discount": "{:.2f}%".format(r["avg_discount_pct"]),
    } for r in sorted(metrics.agent_rollup(transactions),
                      key=lambda r: r["revenue"])]

    exposure_rows = [{
        "exposure": esc(r["exposure"]),
        "units": r["units"],
        "list_ppsf": money(r["avg_list_ppsf"]),
    } for r in metrics.exposure_premium(units)]

    body = """
<section class="tiles">{tiles}</section>

<section>
  <h2>Absorption by project</h2>
  <p class="note">Share of tracked suites that are firm or closed, newest
  launch last.</p>
  {chart}
</section>

<section>
  <h2>Portfolio by project</h2>
  {project_table}
</section>

<section>
  <h2>Pricing by suite model</h2>
  <p class="note">$/sqft is calculated on interior area. Balconies are
  excluded, matching how GTA pre-construction is priced.</p>
  {model_table}
</section>

<section>
  <h2>Sales leaderboard</h2>
  {agent_table}
</section>

<section>
  <h2>Exposure premium</h2>
  <p class="note">Average list $/sqft by compass facing.</p>
  {exposure_table}
</section>
""".format(
        tiles=tiles,
        chart=absorption_chart(rollup),
        project_table=table(project_rows, [
            ("project", "Project", "l"),
            ("neighbourhood", "Neighbourhood", "l"),
            ("launch", "Launch", "l"),
            ("tracked", "Units", "r"),
            ("sold", "Sold", "r"),
            ("available", "Avail", "r"),
            ("absorption", "Absorption", "r"),
            ("list_ppsf", "List/sf", "r"),
            ("sold_ppsf", "Sold/sf", "r"),
            ("revenue", "Revenue", "r"),
        ]),
        model_table=table(model_rows, [
            ("model", "Model", "l"),
            ("units", "Units", "r"),
            ("avg_sqft", "Avg sf", "r"),
            ("avg_list", "Avg list", "r"),
            ("list_ppsf", "List/sf", "r"),
            ("sold_ppsf", "Sold/sf", "r"),
            ("absorption", "Absorption", "r"),
        ]),
        agent_table=table(agent_rows, [
            ("agent", "Agent", "l"),
            ("brokerage", "Brokerage", "l"),
            ("deals", "Deals", "r"),
            ("revenue", "Revenue", "r"),
            ("discount", "Avg discount", "r"),
        ]),
        exposure_table=table(exposure_rows, [
            ("exposure", "Facing", "l"),
            ("units", "Units", "r"),
            ("list_ppsf", "List/sf", "r"),
        ]),
    )

    return page(
        "GTA high-rise sales",
        body,
        subtitle="Eight fictional pre-construction developments across Toronto, "
                 "Vaughan, Mississauga and Pickering.",
        breadcrumb="<span>Portfolio</span>",
    )


def build_project_page(project, units, transactions):
    pid = project["project_id"]
    p_units = [u for u in units if u["project_id"] == pid]
    p_txns = [t for t in transactions if t["project_id"] == pid]
    summary = metrics.project_rollup([project], p_units, p_txns)[0]

    tiles = "".join([
        stat_tile("Revenue", compact_money(summary["revenue"]),
                  "{} deals".format(len(p_txns))),
        stat_tile("Absorption", pct(summary["absorption_pct"]),
                  "{} of {} tracked".format(summary["sold"],
                                            summary["units_tracked"])),
        stat_tile("Avg days to firm", "{:.0f}".format(summary["avg_days_on_market"]),
                  "from launch date"),
        stat_tile("Avg list $/sf", money(summary["avg_list_ppsf"]),
                  "interior area"),
    ])

    suite_rows = [{
        "suite": esc(u["suite"]),
        "floor": u["floor"],
        "model": esc(u["model"]),
        "sqft": "{:,}".format(u["interior_sqft"]),
        "balcony": "{:,}".format(u["balcony_sqft"]),
        "exposure": esc(u["exposure"]),
        "list_price": money(u["list_price"]),
        "ppsf": money(detail_ppsf(u)),
        "status": '<span class="status status-{s}">{s}</span>'.format(
            s=esc(u["status"])),
    } for u in sorted(p_units, key=lambda r: r["suite"])]

    txn_rows = [{
        "date": esc(t["sale_date"]),
        "suite": esc(t["unit_id"].rsplit("-", 1)[-1]),
        "list_price": money(t["list_price"]),
        "sold_price": money(t["sold_price"]),
        "discount": "{:.2f}%".format(
            metrics.discount_pct(t["list_price"], t["sold_price"])),
        "agent": esc(t["agent"]),
        "incentive": esc(t["incentive_package"]),
    } for t in sorted(p_txns, key=lambda r: r["sale_date"])]

    body = """
<section class="tiles">{tiles}</section>

<section>
  <h2>Building</h2>
  <dl class="facts">
    <dt>Municipality</dt><dd>{municipality}</dd>
    <dt>Neighbourhood</dt><dd>{neighbourhood}</dd>
    <dt>Storeys</dt><dd>{storeys}</dd>
    <dt>Total units</dt><dd>{total_units}</dd>
    <dt>Launched</dt><dd>{launch}</dd>
    <dt>Occupancy target</dt><dd>{occupancy}</dd>
  </dl>
  <p class="note">Only a sample of suites is tracked here, so absorption is
  calculated on tracked suites rather than the {total_units}-unit tower.</p>
</section>

<section>
  <h2>Suite inventory</h2>
  {suite_table}
</section>

<section>
  <h2>Transactions</h2>
  {txn_table}
</section>
""".format(
        tiles=tiles,
        municipality=esc(project["municipality"]),
        neighbourhood=esc(project["neighbourhood"]),
        storeys=project["storeys"],
        total_units=project["total_units"],
        launch=esc(project["launch_date"]),
        occupancy=esc(project["occupancy_target"]),
        suite_table=table(suite_rows, [
            ("suite", "Suite", "l"),
            ("floor", "Floor", "r"),
            ("model", "Model", "l"),
            ("sqft", "Interior sf", "r"),
            ("balcony", "Balcony sf", "r"),
            ("exposure", "Facing", "l"),
            ("list_price", "List", "r"),
            ("ppsf", "$/sf", "r"),
            ("status", "Status", "l"),
        ]),
        txn_table=table(txn_rows, [
            ("date", "Sale date", "l"),
            ("suite", "Suite", "l"),
            ("list_price", "List", "r"),
            ("sold_price", "Sold", "r"),
            ("discount", "Discount", "r"),
            ("agent", "Agent", "l"),
            ("incentive", "Incentive", "l"),
        ]),
    )

    return page(
        "{} ({})".format(project["project_name"], pid),
        body,
        subtitle="{}, {}".format(project["neighbourhood"], project["municipality"]),
    )


# --------------------------------------------------------------------------
# static assets
# --------------------------------------------------------------------------

STYLE = """/* Generated by src/build_site.py -- edit the generator, not this file. */
:root {
  color-scheme: light;
  --page:           #f9f9f7;
  --surface:        #fcfcfb;
  --text-primary:   #0b0b0b;
  --text-secondary: #52514e;
  --muted:          #898781;
  --grid:           #e1e0d9;
  --baseline:       #c3c2b7;
  --border:         rgba(11, 11, 11, 0.10);
  --series-1:       #2a78d6;
  --track:          #cde2fb;
  --good:           #0ca30c;
  --warning:        #fab219;
  --critical:       #d03b3b;
  --banner:         #fff8e6;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    color-scheme: dark;
    --page:           #0d0d0d;
    --surface:        #1a1a19;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --muted:          #898781;
    --grid:           #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255, 255, 255, 0.10);
    --series-1:       #3987e5;
    --track:          #0d366b;
    --banner:         #2a2417;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page:           #0d0d0d;
  --surface:        #1a1a19;
  --text-primary:   #ffffff;
  --text-secondary: #c3c2b7;
  --muted:          #898781;
  --grid:           #2c2c2a;
  --baseline:       #383835;
  --border:         rgba(255, 255, 255, 0.10);
  --series-1:       #3987e5;
  --track:          #0d366b;
  --banner:         #2a2417;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--page);
  color: var(--text-primary);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.5;
}

.banner {
  background: var(--banner);
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  font-size: 13px;
  padding: 8px 24px;
  text-align: center;
}

header {
  align-items: center;
  display: flex;
  justify-content: space-between;
  padding: 16px 24px 0;
}
header nav a, header nav span {
  color: var(--text-secondary);
  font-size: 14px;
  text-decoration: none;
}
header nav a:hover { color: var(--series-1); }
#theme {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 13px;
  padding: 4px 12px;
}
#theme:hover { color: var(--text-primary); }

main { margin: 0 auto; max-width: 1100px; padding: 8px 24px 64px; }

h1 { font-size: 28px; font-weight: 600; margin: 16px 0 4px; }
h2 {
  border-bottom: 1px solid var(--grid);
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px;
  padding-bottom: 6px;
}
.subtitle { color: var(--text-secondary); margin: 0 0 8px; max-width: 65ch; }
.note { color: var(--text-secondary); font-size: 13px; margin: -4px 0 12px; max-width: 70ch; }
.empty { color: var(--muted); font-style: italic; }
section { margin-top: 36px; }

/* stat tiles */
.tiles {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  margin-top: 24px;
}
.tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.tile-label { color: var(--text-secondary); font-size: 13px; }
.tile-value { font-size: 30px; font-weight: 600; letter-spacing: -0.5px; margin-top: 2px; }
.tile-note { color: var(--muted); font-size: 12px; }

/* bar chart -- single series, no legend needed */
.chart {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
}
.chart-scale {
  color: var(--muted);
  display: flex;
  font-size: 11px;
  justify-content: space-between;
  margin: 0 0 8px 56px;
  font-variant-numeric: tabular-nums;
}
.bar-row { align-items: center; display: flex; gap: 10px; padding: 3px 0; }
.bar-label {
  color: var(--text-secondary);
  flex: 0 0 46px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.bar-track {
  background: var(--track);
  border-radius: 0 4px 4px 0;
  flex: 1 1 auto;
  height: 18px;
  overflow: hidden;
}
.bar-fill {
  background: var(--series-1);
  border-radius: 0 4px 4px 0;
  height: 100%;
  transition: width 0.2s ease;
}
.bar-value {
  flex: 0 0 52px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.bar-row:hover .bar-fill { filter: brightness(1.08); }

/* tables */
.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow-x: auto;
}
table { border-collapse: collapse; font-size: 14px; width: 100%; }
caption { color: var(--text-secondary); padding: 10px; text-align: left; }
th, td {
  border-bottom: 1px solid var(--grid);
  padding: 8px 12px;
  text-align: left;
  white-space: nowrap;
}
th {
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  user-select: none;
}
th:hover { color: var(--text-primary); }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: color-mix(in srgb, var(--series-1) 6%, transparent); }
td a { color: var(--series-1); text-decoration: none; }
td a:hover { text-decoration: underline; }

/* status pills -- colour is never the only cue, the label is always present */
.status {
  border-radius: 4px;
  font-size: 12px;
  padding: 2px 7px;
}
.status-available { background: color-mix(in srgb, var(--good) 15%, transparent); }
.status-held      { background: color-mix(in srgb, var(--warning) 22%, transparent); }
.status-firm      { background: color-mix(in srgb, var(--series-1) 15%, transparent); }
.status-closed    { background: color-mix(in srgb, var(--baseline) 35%, transparent); }

/* project facts */
.facts {
  display: grid;
  gap: 2px 16px;
  grid-template-columns: max-content 1fr;
  margin: 0 0 12px;
}
.facts dt { color: var(--text-secondary); font-size: 13px; }
.facts dd { margin: 0; }

footer {
  border-top: 1px solid var(--grid);
  color: var(--muted);
  font-size: 12px;
  margin: 0 auto;
  max-width: 1100px;
  padding: 16px 24px 32px;
}
footer code { font-size: 11px; }

/* tooltip */
#tip {
  background: var(--text-primary);
  border-radius: 6px;
  color: var(--surface);
  font-size: 12px;
  opacity: 0;
  padding: 5px 9px;
  pointer-events: none;
  position: fixed;
  transition: opacity 0.1s ease;
  white-space: nowrap;
  z-index: 10;
}
#tip.on { opacity: 1; }
"""

APP_JS = """/* Generated by src/build_site.py -- edit the generator, not this file. */
(function () {
  "use strict";

  /* Theme toggle. An explicit choice wins over the OS setting, both ways. */
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem("theme"); } catch (e) { /* private mode */ }
  if (saved) { root.setAttribute("data-theme", saved); }

  var button = document.getElementById("theme");
  if (button) {
    button.addEventListener("click", function () {
      var dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      var current = root.getAttribute("data-theme") || (dark ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) { /* ignore */ }
    });
  }

  /* Hover tooltips on the chart rows. */
  var tip = document.getElementById("tip");
  function showTip(event) {
    var text = event.currentTarget.getAttribute("data-tip");
    if (!tip || !text) { return; }
    tip.innerHTML = text;
    tip.classList.add("on");
    tip.setAttribute("aria-hidden", "false");
    var box = event.currentTarget.getBoundingClientRect();
    tip.style.left = Math.min(event.clientX + 12, window.innerWidth - tip.offsetWidth - 8) + "px";
    tip.style.top = (box.top - tip.offsetHeight - 6) + "px";
  }
  function hideTip() {
    if (!tip) { return; }
    tip.classList.remove("on");
    tip.setAttribute("aria-hidden", "true");
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-tip]"), function (el) {
    el.addEventListener("mousemove", showTip);
    el.addEventListener("mouseleave", hideTip);
  });

  /* Click a column header to sort. Numbers sort numerically. */
  function cellValue(row, index) {
    var text = row.children[index].textContent.trim();
    var numeric = text.replace(/[$,%\\s]/g, "");
    return numeric !== "" && !isNaN(numeric) ? parseFloat(numeric) : text.toLowerCase();
  }

  Array.prototype.forEach.call(document.querySelectorAll("table"), function (tableEl) {
    var headers = tableEl.querySelectorAll("thead th");
    Array.prototype.forEach.call(headers, function (header, index) {
      header.addEventListener("click", function () {
        var body = tableEl.querySelector("tbody");
        var rows = Array.prototype.slice.call(body.rows);
        var descending = header.dataset.dir !== "desc";
        rows.sort(function (a, b) {
          var av = cellValue(a, index);
          var bv = cellValue(b, index);
          if (av < bv) { return descending ? 1 : -1; }
          if (av > bv) { return descending ? -1 : 1; }
          return 0;
        });
        Array.prototype.forEach.call(headers, function (h) { delete h.dataset.dir; });
        header.dataset.dir = descending ? "desc" : "asc";
        rows.forEach(function (row) { body.appendChild(row); });
      });
    });
  });
})();
"""


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------

def build(out_dir=DEFAULT_OUT):
    """Write the whole site to out_dir. Returns the list of files written."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    projects = load_projects()
    units = load_units()
    transactions = load_transactions()

    written = []

    index = out_dir / "index.html"
    index.write_text(build_index(projects, units, transactions))
    written.append(index)

    for project in projects:
        path = out_dir / "project-{}.html".format(project["project_id"])
        path.write_text(build_project_page(project, units, transactions))
        written.append(path)

    style = out_dir / "style.css"
    style.write_text(STYLE)
    written.append(style)

    app = out_dir / "app.js"
    app.write_text(APP_JS)
    written.append(app)

    # Tell GitHub Pages not to run the output through Jekyll.
    nojekyll = out_dir / ".nojekyll"
    nojekyll.write_text("")
    written.append(nojekyll)

    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the static sales dashboard.")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="output directory (default: ./site)")
    args = parser.parse_args(argv)

    written = build(args.out)
    print("Wrote {} files to {}/".format(len(written), args.out))
    for path in written:
        print("  {}".format(path.name))


if __name__ == "__main__":
    main()
