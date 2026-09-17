# Data dictionary

All data is synthetic. See the warning in [README.md](../README.md).

## `data/projects.csv`

One row per development. 8 rows.

| Column | Type | Notes |
| --- | --- | --- |
| `project_id` | text | Primary key, format `GG-NN` |
| `project_name` | text | Fictional development name |
| `municipality` | text | Toronto, Vaughan, Mississauga, Pickering |
| `neighbourhood` | text | Sub-market — the real driver of $/sqft |
| `storeys` | integer | Tower height |
| `total_units` | integer | Full unit count in the building |
| `launch_date` | date | `YYYY-MM-DD`. Public sales launch |
| `occupancy_target` | text | Quarter format, e.g. `2029 Q2` |

`total_units` is the whole building; only a sample of suites appears in
`unit_inventory.csv`, so absorption here is calculated on *tracked* units, not
the full tower.

## `data/unit_inventory.csv`

One row per tracked suite. 64 rows.

| Column | Type | Notes |
| --- | --- | --- |
| `unit_id` | text | Primary key, format `GG-NN-SUITE` |
| `project_id` | text | → `projects.project_id` |
| `suite` | text | Suite number. Floor + unit position |
| `floor` | integer | Higher floors carry a price premium |
| `model` | text | `Studio`, `1B`, `1B+D`, `2B`, `2B+D`, `3B` (D = den) |
| `beds` | integer | 0 for a studio |
| `baths` | integer | |
| `interior_sqft` | integer | **Pricing is based on this**, not total area |
| `balcony_sqft` | integer | Outdoor area. Excluded from $/sqft |
| `exposure` | text | Compass facing. `N`,`S`,`E`,`W`,`NE`,`NW`,`SE`,`SW` |
| `list_price` | integer | Canadian dollars, no cents |
| `status` | text | `available`, `held`, `firm`, `closed` |

## `data/sales_transactions.csv`

One row per deal. 28 rows, sorted by sale date. Only suites with status `firm`
or `closed` appear here — enforced by a test.

| Column | Type | Notes |
| --- | --- | --- |
| `txn_id` | text | Primary key, format `TXN-NNNN`, numbered in date order |
| `unit_id` | text | → `unit_inventory.unit_id` |
| `project_id` | text | → `projects.project_id`. Denormalised for convenience |
| `sale_date` | date | `YYYY-MM-DD`. Always on or after the project launch |
| `list_price` | integer | Price at time of sale |
| `sold_price` | integer | What it actually traded at. ≤ list |
| `agent` | text | Fictional sales rep |
| `brokerage` | text | `In-House Presentation Centre` = direct sale |
| `incentive_package` | text | Capped dev charges, décor dollars, parking, etc. |
| `deposit_structure` | text | Deposit schedule offered |
| `status` | text | Mirrors the unit's `firm` / `closed` |

## Relationships

```
projects.project_id
    ├──< unit_inventory.project_id
    │        └──< sales_transactions.unit_id
    └──< sales_transactions.project_id
```

`tests/test_metrics.py::TestDataIntegrity` enforces referential integrity,
unique keys, positive prices, and sale-after-launch dates. If you hand-edit a
CSV and break a link, the tests will tell you.
