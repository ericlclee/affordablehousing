"""
sim_parameters.py  -  House London #2 hackathon (26 Sep 2026)

Turns data/foundations.parquet (181,929 London planning applications, 2022-2025,
PlanIt-style fields) into numbers the planning-process simulator can use:

  (a) decision time + refusal rate by app_type and size band (Full, Outline)
  (b) Section 106 / legal-agreement signals and their effect on decision time
  (c) committee vs delegated decisions: time and refusal
  (d) residents: n_comments distribution and refusal by comment band
  (e) withdrawal rate by size
  (f) post-approval burden: 'Conditions' (and 'Amendment') applications per parent scheme
  (g) borough variation for Full applications with n_dwellings >= 10

Run from the project root:
    .venv/bin/python analysis/sim_parameters.py
Prints every table and writes analysis/sim_parameters.json (for the web app).

Definitions used everywhere:
  approved  = status in ('Permitted','Conditions')   # status 'Conditions' = granted with conditions
  refused   = status = 'Rejected'
  refusal_rate    = refused / (approved + refused)
  withdrawal_rate = withdrawn / (approved + refused + withdrawn)
  days = days_to_decision (= decided_date - start_date), only rows with days >= 0
"""
import json
import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "foundations.parquet"
OUT_JSON = ROOT / "analysis" / "sim_parameters.json"

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 80)

con = duckdb.connect()
con.execute(f"create table raw as select * from read_parquet('{PARQUET.as_posix()}')")

# --- regexes ---------------------------------------------------------------
# NB: plain 'subject to' is useless: 'Approve subject to conditions' is the most common grant wording.
S106_RE = (r"section\s*106|s\.?\s?106|legal agreement|unilateral undertaking|planning obligation"
           r"|deed of variation|subject to (the )?(completion|signing|prior completion)")
COMMITTEE_RE = r"committee|commitee|planning board|full council"

# Trap: some boroughs (esp. Wandsworth) label condition-discharge and s73 variation
# applications as app_type 'Full', and those rows inherit the PARENT scheme's n_dwellings.
# We reclassify by description text; the original label is kept as app_type_raw.
AMEND_RE = (r"variation of condition|vary condition|removal of condition|remove condition"
            r"|non.material amendment|minor.material amendment|section 73|s\.?\s?73")
DISCH_RE = (r"pursuant to (part .{0,30} of )?condition|discharge of (condition|details)|discharge condition"
            r"|approval of details|details (of|for|in respect of|required by|reserved by|pursuant).{0,250}condition \d")
con.execute(f"""
create table raw2 as
select * replace (
  case when app_type in ('Full','Outline') and regexp_matches(lower(coalesce(description,'')), '{AMEND_RE}') then 'Amendment'
       when app_type in ('Full','Outline') and regexp_matches(lower(coalesce(description,'')), '{DISCH_RE}') then 'Conditions'
       else app_type end as app_type),
  app_type as app_type_raw
from raw
""")
con.execute(f"""
create table f as
select *,
  case when status in ('Permitted','Conditions') then 1
       when status = 'Rejected' then 0 end                         as ok,          -- 1 approved, 0 refused, null otherwise
  (status = 'Withdrawn')::int                                        as wd,
  case when status in ('Permitted','Conditions','Rejected','Withdrawn') then 1 end as closed,
  case when days_to_decision >= 0 then days_to_decision end           as days,
  case when decided_date > target_decision_date then 1
       when decided_date is not null and target_decision_date is not null then 0 end as late,
  coalesce(nullif(app_size,''),'(blank)')                             as size,
  case when n_dwellings >= 150 then '4: 150+'
       when n_dwellings >= 50  then '3: 50-149'
       when n_dwellings >= 10  then '2: 10-49'
       when n_dwellings >= 1   then '1: 1-9'
       else '0: n/a' end                                              as dw_band,
  regexp_matches(lower(coalesce(decision,'')),    '{S106_RE}')        as s106_decision,
  regexp_matches(lower(coalesce(description,'')), '{S106_RE}')        as s106_description,
  regexp_matches(lower(coalesce(description,'')), 'outline (planning )?(application|permission)') as true_outline,
  regexp_matches(lower(coalesce(description,'')), 'lawful|prior approval|prior notification') as ldc_or_prior,
  case when regexp_matches(lower(coalesce(decided_by,'')), 'withdraw') then 'withdrawn-label'
       when regexp_matches(lower(coalesce(decided_by,'')), '{COMMITTEE_RE}')
            and not regexp_matches(lower(decided_by), 'deleg')   then 'committee'
       when regexp_matches(lower(coalesce(decided_by,'')), 'deleg') then 'delegated'
       when decided_by is null or decided_by = '' then 'unknown'
       else 'other' end                                               as route
from raw2
""")

# boroughs where n_comments is actually populated (it is all-or-nothing per borough)
con.execute("""
create table comment_boroughs as
select area_name from f group by 1 having count(n_comments) = count(*)
""")

RESULTS = {}


def q(title, sql, key=None):
    df = con.execute(sql).fetchdf()
    print(f"\n=== {title} ===")
    print(df.to_string(index=False))
    if key:
        RESULTS[key] = json.loads(df.to_json(orient="records"))
    return df


STATS = """
  count(*)                                         as n,
  count(ok)                                        as decided,
  round(1 - avg(ok), 3)                            as refusal_rate,
  round(sum(wd) / nullif(sum(closed),0), 3)        as withdrawal_rate,
  round(median(days) filter (where ok is not null))                     as med_days,
  round(quantile_cont(days, 0.25) filter (where ok is not null))        as p25_days,
  round(quantile_cont(days, 0.75) filter (where ok is not null))        as p75_days,
  round(quantile_cont(days, 0.90) filter (where ok is not null))        as p90_days,
  round(avg(late) filter (where ok is not null), 3)                    as share_after_target_date
"""

# ---------------------------------------------------------------- overview / traps
q("trap check: Full/Outline rows reclassified by description text",
  """select area_name, app_type_raw, app_type, count(*) n, count(n_dwellings) with_dwellings
     from f where app_type_raw in ('Full','Outline') and app_type <> app_type_raw
     group by all order by n desc limit 15""", "reclass_top")
q("trap check: reclassification totals",
  """select app_type_raw, app_type, count(*) n, count(*) filter (where n_dwellings>=10) n_10plus_dw
     from f where app_type_raw in ('Full','Outline') group by all order by 1,2""", "reclass_totals")
q("overview: status counts", "select status, count(*) n from f group by 1 order by 2 desc", "status_counts")
q("trap check: what 'Outline' really contains",
  """select app_type, count(*) n, sum(true_outline::int) mentions_outline_permission,
            sum(ldc_or_prior::int) mentions_lawful_or_prior_approval
     from f where app_type in ('Full','Outline') group by 1""", "outline_trap")

# ---------------------------------------------------------------- (a)
q("(a1) Full & Outline by app_size",
  f"select app_type, size, {STATS} from f where app_type in ('Full','Outline') group by all order by 1,2",
  "a_by_app_size")
q("(a2) Full by dwelling band (n_dwellings only filled for ~7.9k rows)",
  f"select app_type, dw_band, {STATS} from f where app_type in ('Full','Outline') and n_dwellings is not null group by all order by 1,2",
  "a_by_dwelling_band")
q("(a3) genuine outline planning applications (description says 'outline planning application/permission')",
  f"select size, {STATS} from f where true_outline and app_type in ('Full','Outline') group by all order by 1",
  "a_true_outline")

# ---------------------------------------------------------------- (b)
q("(b1) S106 / legal-agreement signal counts (all app types)",
  """select count(*) filter (where s106_decision) decision_mentions,
            count(*) filter (where s106_description) description_mentions,
            count(*) filter (where s106_decision or s106_description) either
     from f""", "b_counts")
q("(b2) approved Full applications: median days with vs without S106 wording in the DECISION text, by size",
  """select size, s106_decision,
            count(*) n_approved,
            round(median(days)) med_days, round(quantile_cont(days,0.75)) p75_days,
            round(quantile_cont(days,0.9)) p90_days, round(avg(late),3) share_after_target
     from f where app_type='Full' and ok=1 group by all order by 1,2""", "b_decision_text")
q("(b3) Full applications with n_dwellings>=10: S106 wording in decision OR description",
  """select (s106_decision or s106_description) s106_any, count(*) n, count(ok) decided,
            round(1-avg(ok),3) refusal_rate,
            round(median(days) filter (where ok=1)) med_days_approved,
            round(quantile_cont(days,0.9) filter (where ok=1)) p90_days_approved
     from f where app_type='Full' and n_dwellings>=10 group by 1""", "b_major_housing")
q("(b4) boroughs whose decision text ever mentions S106 (the signal is borough-specific wording)",
  """select area_name, count(*) filter (where s106_decision) s106_decisions,
            count(*) filter (where app_type='Full' and size='Large') full_large
     from f group by 1 having count(*) filter (where s106_decision) > 0 order by 2 desc""", "b_by_borough")

# ---------------------------------------------------------------- (c)
q("(c1) decision route label counts", "select route, count(*) n from f group by 1 order by 2 desc", "c_route_counts")
q("(c2) committee vs delegated: Full applications by size",
  f"select size, route, {STATS} from f where app_type='Full' and route in ('committee','delegated') group by all order by 1,2",
  "c_route_by_size")
q("(c3) committee vs delegated: Full, n_dwellings>=10",
  f"select route, {STATS} from f where app_type='Full' and n_dwellings>=10 and route in ('committee','delegated','unknown','other') group by all order by 1",
  "c_route_major_housing")

# ---------------------------------------------------------------- (d)
q("(d0) boroughs with n_comments populated", "select * from comment_boroughs order by 1", "d_comment_boroughs")
q("(d1) n_comments distribution (populated boroughs), Full apps by size",
  """select size, count(*) n,
            round(avg((n_comments=0)::int),3) share_zero,
            quantile_cont(n_comments,0.5) p50, quantile_cont(n_comments,0.75) p75,
            quantile_cont(n_comments,0.9) p90, quantile_cont(n_comments,0.99) p99, max(n_comments) max,
            round(avg(n_comments),2) mean
     from f where app_type='Full' and area_name in (select area_name from comment_boroughs)
     group by 1 order by 1""", "d_distribution")
CB = """case when n_comments=0 then '0' when n_comments<=2 then '1-2' when n_comments<=9 then '3-9'
             when n_comments<=24 then '10-24' when n_comments<=99 then '25-99' else '100+' end"""
q("(d2) refusal rate by comment band x app_size (Full, populated boroughs)",
  f"""select size, {CB} comment_band, count(ok) decided, round(1-avg(ok),3) refusal_rate,
             round(median(days) filter (where ok is not null)) med_days,
             round(sum(wd)/nullif(sum(closed),0),3) withdrawal_rate
      from f where app_type='Full' and area_name in (select area_name from comment_boroughs) and size in ('Small','Medium','Large')
      group by all order by 1, min(n_comments)""", "d_refusal_by_band")
q("(d3) refusal rate by comment band, Full with n_dwellings>=10 (populated boroughs)",
  f"""select {CB} comment_band, count(ok) decided, round(1-avg(ok),3) refusal_rate,
             round(median(days) filter (where ok is not null)) med_days
      from f where app_type='Full' and n_dwellings>=10 and area_name in (select area_name from comment_boroughs)
      group by all order by min(n_comments)""", "d_major_housing")

# ---------------------------------------------------------------- (e)
q("(e1) withdrawal rate by app_type x size (Full/Outline)",
  """select app_type, size, sum(closed) closed, sum(wd) withdrawn, round(sum(wd)/sum(closed),3) withdrawal_rate
     from f where app_type in ('Full','Outline') group by all order by 1,2""", "e_by_size")
q("(e2) withdrawal rate by dwelling band (Full)",
  """select dw_band, sum(closed) closed, sum(wd) withdrawn, round(sum(wd)/sum(closed),3) withdrawal_rate
     from f where app_type='Full' and n_dwellings is not null group by all order by 1""", "e_by_dwelling_band")

# ---------------------------------------------------------------- (f) post-approval burden
post = con.execute("""
select area_name, uid, app_type, description, start_date, status
from f where app_type in ('Conditions','Amendment')
""").fetchdf()
parents = con.execute("""
select area_name, upper(uid) puid, app_type p_type, size p_size, n_dwellings p_dw, decided_date p_decided
from f where app_type not in ('Conditions','Amendment')
""").fetchdf()

TOKEN = re.compile(r"\b[A-Z0-9]*\d[A-Z0-9]*(?:/[A-Z0-9]+)+\b|\b\d{6}[A-Z]{0,4}\b", re.I)
DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")


def parent_ref(row):
    own = str(row.uid).upper()
    for t in TOKEN.findall(str(row.description or "")):
        t = t.upper().rstrip(".")
        if DATE.match(t) or t == own or not re.search(r"\d{2,}", t):
            continue
        return t
    return None


post["parent"] = post.apply(parent_ref, axis=1)
post = post.merge(parents, how="left", left_on=["area_name", "parent"], right_on=["area_name", "puid"])
con.register("post", post)

q("(f1) parent-reference extraction coverage",
  """select app_type, count(*) n, count(parent) with_parent_ref, round(count(parent)/count(*),3) share_with_ref,
            count(puid) parent_in_dataset
     from post group by 1""", "f_coverage")
q("(f2) post-approval applications per parent scheme (grouped by extracted parent ref)",
  """with g as (select area_name, parent, count(*) filter (where app_type='Conditions') n_cond,
                       count(*) filter (where app_type='Amendment') n_amend
                from post where parent is not null group by 1,2)
     select count(*) schemes,
            round(avg(n_cond) filter (where n_cond>0),2) mean_cond_apps,
            median(n_cond) filter (where n_cond>0) median_cond_apps,
            quantile_cont(n_cond,0.9) filter (where n_cond>0) p90_cond_apps,
            max(n_cond) max_cond_apps,
            round(avg(n_amend) filter (where n_amend>0),2) mean_amend_apps,
            max(n_amend) max_amend_apps
     from g""", "f_per_scheme")
q("(f3) conditions apps per scheme by PARENT size (parent found in dataset)",
  """with g as (select area_name, parent, any_value(p_size) p_size,
                       case when any_value(p_dw)>=10 then 'parent 10+ dwellings' else 'other/unknown' end p_dw_band,
                       count(*) filter (where app_type='Conditions') n_cond,
                       count(*) filter (where app_type='Amendment') n_amend
                from post where puid is not null group by 1,2)
     select p_size, p_dw_band, count(*) schemes, round(avg(n_cond),2) mean_cond, quantile_cont(n_cond,0.9) p90_cond,
            round(avg(n_amend),2) mean_amend, max(n_cond) max_cond
     from g group by all order by 1,2""", "f_by_parent_size")
q("(f4) conditions apps: refusal rate and median days",
  f"select app_type, {STATS} from f where app_type in ('Conditions','Amendment') group by 1", "f_stage_stats")

# ---------------------------------------------------------------- (g)
q("(g) borough variation: Full applications with n_dwellings >= 10",
  """select area_name, count(*) n, count(ok) decided, round(1-avg(ok),3) refusal_rate,
            round(sum(wd)/nullif(sum(closed),0),3) withdrawal_rate,
            round(median(days) filter (where ok is not null)) med_days,
            round(quantile_cont(days,0.9) filter (where ok is not null)) p90_days,
            round(avg((route='committee')::int),3) committee_share,
            round(avg((s106_decision or s106_description)::int),3) s106_share,
            round(median(n_dwellings)) med_dwellings
     from f where app_type='Full' and n_dwellings>=10
     group by 1 having count(ok) >= 10 order by refusal_rate desc""", "g_boroughs")
q("(g-summary) spread across boroughs (>=10 decided)",
  """with b as (select area_name, 1-avg(ok) rr, median(days) filter (where ok is not null) md, count(ok) d
               from f where app_type='Full' and n_dwellings>=10 group by 1 having count(ok)>=10)
     select count(*) boroughs, round(min(rr),3) min_refusal, round(median(rr),3) median_refusal, round(max(rr),3) max_refusal,
            min(md) min_med_days, median(md) median_med_days, max(md) max_med_days from b""", "g_summary")
q("(g-pooled) all Full, n_dwellings>=10, pooled",
  f"select {STATS} from f where app_type='Full' and n_dwellings>=10", "g_pooled")

# ---------------------------------------------------------------- censoring check
q("(h1) status mix for big schemes (many still Undecided -> medians above are biased low)",
  """select case when n_dwellings>=10 then 'Full 10+ dwellings' else 'Full Large (any)' end grp, status, count(*) n
     from f where app_type='Full' and (n_dwellings>=10 or size='Large') group by all order by 1, 3 desc""", "h_status_mix")
q("(h2) 2022-2023 starters only (mostly resolved): Full by size",
  f"select size, {STATS}, round(avg((status='Undecided')::int),3) share_still_undecided from f where app_type='Full' and year(start_date)<=2023 group by 1 order by 1",
  "h_cohort_2022_23")
q("(h3) 2022-2023 starters: Full with n_dwellings>=10",
  f"select {STATS}, round(avg((status='Undecided')::int),3) share_still_undecided from f where app_type='Full' and n_dwellings>=10 and year(start_date)<=2023",
  "h_cohort_major_housing")
q("(f5) the five parent refs with the most Conditions applications",
  """select area_name, parent, count(*) n_cond, any_value(p_size) parent_size, any_value(p_dw) parent_dwellings
     from post where app_type='Conditions' and parent is not null group by 1,2 order by 3 desc limit 5""", "f_top_parents")

OUT_JSON.write_text(json.dumps(RESULTS, indent=1, default=str))
print(f"\nwrote {OUT_JSON}")
