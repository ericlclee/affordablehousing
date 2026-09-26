"""Independent arithmetic check of Proposal 106 (PROPOSAL106_SPEC.md, stages 0, 2, 4, 5, vision).

Written from the spec only, without reading the app's engine. Run:
  .venv/bin/python proposal106/check_engine.py
Interpretation choices (spec is silent) are flagged with 'ASSUMPTION'.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SIZES = {"b1": 50.0, "b2": 70.0, "b3": 86.0}   # m2 NIA, London Plan Table 3.1
HAB = {"b1": 2, "b2": 3, "b3": 4}              # habitable rooms per home
NET_TO_GROSS = 0.80

ASSUMPTIONS = {
    "sale": {"low": 7200.0, "base": 8000.0, "high": 9000.0},
    "sr_value": 2987.0,
    "so_value": 4500.0,
    "build_low": 2014.0,     # up to 5 storeys
    "build_high": 2364.0,    # above 5 storeys
    "contingency": 0.10,
    "fees": 0.10,
    "sales_cost": 0.0275,
    "mcil": 72.73,
    "bcil": 0.0,
    "s106_per_home": 0.0,
    "finance_rate": 0.065,
    "finance_years": 2.0,
    "land": 12_000_000.0,
    "target_return": 0.175,
}


def site_area():
    try:
        with open(os.path.join(HERE, "data", "site.json")) as f:
            s = json.load(f)
        return {
            "polygon_area_m2": float(s.get("polygon_area_m2")) if s.get("polygon_area_m2") else None,
            "hectares_m2": float(s["hectares"]) * 10000 if s.get("hectares") else None,
        }
    except Exception:
        return {"polygon_area_m2": None, "hectares_m2": 5100.0}


def massing(p):
    site = p["site_area_m2"]
    gia = site * (p["podium_coverage"] * p["podium_storeys"] + p["tower_coverage"] * p["tower_storeys"])
    nia = NET_TO_GROSS * gia
    mix = {"b1": p["mix_b1"], "b2": p["mix_b2"], "b3": p["mix_b3"]}
    tot = sum(mix.values())
    mix = {k: v / tot for k, v in mix.items()}
    avg_size = sum(mix[k] * SIZES[k] for k in mix)
    homes = nia / avg_size
    avg_hab = sum(mix[k] * HAB[k] for k in mix)
    hab_rooms = homes * avg_hab
    storeys = p["podium_storeys"] + (p["tower_storeys"] if p["tower_coverage"] > 0 else 0)
    height = storeys * p["floor_to_floor"]
    # ASSUMPTION: tower sits on the podium, so ground footprint = max(podium, tower) coverage
    footprint = max(p["podium_coverage"], p["tower_coverage"])
    open_space = site * (1 - footprint)
    child = homes * (mix["b2"] * 0.2 + mix["b3"] * 0.6)
    return dict(gia=gia, nia=nia, homes=homes, hab_rooms=hab_rooms, avg_size=avg_size, avg_hab=avg_hab,
                storeys=storeys, height=height, open_space=open_space, open_share=1 - footprint,
                play_need_m2=10 * child, mix=mix)


def appraisal(p, a=ASSUMPTIONS, case="base", build_rule="whole"):
    m = massing(p)
    aff = p["affordable_hr_pct"] / 100.0
    sr = p["social_rent_share"] / 100.0
    # ASSUMPTION: affordable homes take the same mix as market, so share of hab rooms == share of NIA
    aff_nia = aff * m["nia"]
    market_nia = m["nia"] - aff_nia
    sr_nia = aff_nia * sr
    so_nia = aff_nia * (1 - sr)
    aff_receipts = sr_nia * a["sr_value"] + so_nia * a["so_value"]
    sale = a["sale"][case]
    market_gdv = market_nia * sale
    gdv = market_gdv + aff_receipts
    # Build rate. 'whole' = one rate for the whole GIA by building height (primary reading).
    if build_rule == "whole":
        rate = a["build_low"] if m["storeys"] <= 5 else a["build_high"]
        build_base = m["gia"] * rate
    else:  # 'split': floors 1-5 at low rate, above at high rate (pro rata by storey)
        site = p["site_area_m2"]
        floors = []
        for s in range(1, int(p["podium_storeys"]) + 1):
            floors.append(site * p["podium_coverage"])
        for s in range(1, int(p["tower_storeys"]) + 1):
            floors.append(site * p["tower_coverage"])
        build_base = sum(f * (a["build_low"] if i < 5 else a["build_high"]) for i, f in enumerate(floors))
    build = build_base * (1 + a["contingency"])
    fees = a["fees"] * build
    sales = a["sales_cost"] * market_gdv
    mcil = a["mcil"] * m["gia"]
    bcil = a["bcil"] * m["gia"]
    s106 = a["s106_per_home"] * m["homes"]
    finance = a["finance_rate"] * (a["land"] + 0.5 * build) * a["finance_years"]
    land = a["land"]
    total_cost = build + fees + sales + mcil + bcil + s106 + finance + land
    target = a["target_return"] * gdv
    surplus = gdv - total_cost - target
    profit = gdv - total_cost
    # Break-even market GBP/m2, fixed-point iteration x5 as the spec says
    fixed = build + fees + mcil + bcil + s106 + finance + land
    be = sale
    for _ in range(5):
        g = market_nia * be + aff_receipts
        be = (fixed + a["sales_cost"] * market_nia * be + a["target_return"] * g - aff_receipts) / market_nia if market_nia > 0 else float("inf")
    closed = (fixed - (1 - a["target_return"]) * aff_receipts) / ((1 - a["target_return"] - a["sales_cost"]) * market_nia) if market_nia > 0 else float("inf")
    return dict(m, aff_nia=aff_nia, market_nia=market_nia, sr_nia=sr_nia, so_nia=so_nia,
                aff_receipts=aff_receipts, market_gdv=market_gdv, gdv=gdv, build=build, build_base=build_base,
                fees=fees, sales=sales, mcil=mcil, finance=finance, land=land, total_cost=total_cost,
                target=target, surplus=surplus, profit=profit, profit_on_gdv=profit / gdv if gdv else 0,
                breakeven=be, breakeven_closed=closed,
                sr_homes=m["homes"] * aff * sr)


def route(land_type, aff_pct, sr_share_pct):
    lcr = sr_share_pct
    inter = 100 - sr_share_pct
    public = land_type in ("public", "industrial")
    temp = (aff_pct >= 35) if public else (aff_pct >= 20 and sr_share_pct >= 60)
    ft = aff_pct >= (50 if public else 35) and lcr >= 30 and inter >= 30
    if temp and ft:
        r = "Temporary route AND H5 Fast Track both qualify"
    elif temp:
        r = "Temporary route"
    elif ft:
        r = "H5 Fast Track"
    else:
        r = "H5 Viability Tested (requires review)"
    return dict(temporary=temp, fast_track=ft, route=r)


def mayor(homes, height_m, storeys):
    return dict(
        notified=homes >= 50,
        referable=homes >= 150 or height_m > 30,
        tall=storeys > 6 or height_m > 18,
    )


def vision(seed, cur):
    def rel(k):
        return abs(cur[k] - seed[k]) / seed[k] if seed[k] else 0
    v = 1 - (0.3 * rel("storeys") + 0.3 * rel("podium_coverage") + 0.2 * rel("homes") + 0.2 * rel("open_space"))
    return max(0.0, min(1.0, v))


DEFAULT = dict(podium_coverage=0.55, podium_storeys=6, tower_coverage=0.15, tower_storeys=8,
               floor_to_floor=3.2, mix_b1=40, mix_b2=40, mix_b3=20, affordable_hr_pct=20,
               social_rent_share=60, land_type="private")


def main():
    sa = site_area()
    out = {"site_area_sources": sa}
    for label, area in (("polygon", sa["polygon_area_m2"]), ("hectares", sa["hectares_m2"])):
        if area is None:
            continue
        out[label] = {}
        for aff in (20, 35, 50):
            p = dict(DEFAULT, site_area_m2=area, affordable_hr_pct=aff)
            r = appraisal(p)
            out[label][aff] = {k: r[k] for k in ("gia", "nia", "homes", "hab_rooms", "market_nia", "aff_receipts",
                                                   "gdv", "total_cost", "surplus", "breakeven", "breakeven_closed",
                                                   "build", "fees", "sales", "mcil", "finance", "target",
                                                   "profit_on_gdv", "sr_homes", "height", "storeys", "open_space",
                                                   "play_need_m2")}
            rs = appraisal(p, build_rule="split")
            out[label][aff]["alt_split_build_total_cost"] = rs["total_cost"]
            out[label][aff]["alt_split_build_surplus"] = rs["surplus"]
            out[label][aff]["alt_split_build_breakeven"] = rs["breakeven"]
        # Stage 4 best offer (highest affordable % keeping surplus >= 0, base)
        best = None
        for aff in range(0, 51):
            p = dict(DEFAULT, site_area_m2=area, affordable_hr_pct=aff)
            if appraisal(p)["surplus"] >= 0:
                best = aff
        out[label]["best_offer_int_pct"] = best
    out["routes"] = {
        "private 20 SR60": route("private", 20, 60),
        "private 20 SR40": route("private", 20, 40),
        "public 20 SR60": route("public", 20, 60),
        "public 35 SR60": route("public", 35, 60),
        "private 35 SR60 (60/40)": route("private", 35, 60),
        "private 35 SR40 (40/60)": route("private", 35, 40),
        "private 35 SR30 (30/70)": route("private", 35, 30),
        "private 35 SR25 (25/75)": route("private", 35, 25),
    }
    out["mayor"] = {
        "homes 49 h 29": mayor(49, 29, 9),
        "homes 50 h 29": mayor(50, 29, 9),
        "homes 150 h 29": mayor(150, 29, 9),
        "homes 49 h 31": mayor(49, 31, 9),
    }
    json.dump(out, sys.stdout, indent=1, default=float)


if __name__ == "__main__":
    main()


def utilities(p, seed_m, median=9.0):
    r = appraisal(p)
    u_dev = max(0.0, min(1.0, r["profit_on_gdv"] / 0.25))
    u_plan = min(1.0, p["affordable_hr_pct"] / 50.0)
    x = (r["height"] / median - 1) / 4
    u_res = 0.5 * (1 - max(0.0, min(1.0, x))) + 0.5 * min(1.0, r["open_share"] / 0.5)
    cur = dict(storeys=r["storeys"], podium_coverage=p["podium_coverage"], homes=r["homes"], open_space=r["open_space"])
    u_arch = vision(seed_m, cur)
    return dict(dev=u_dev, plan=u_plan, res=u_res, arch=u_arch), r


def sweep(vision_p, walk, include_res=True, median=9.0):
    """ASSUMPTION: total storeys s in 2..S0+6; tower keeps its share of storeys (round) and its
    coverage ratio to the podium; social rent share fixed at the vision's."""
    vm = massing(vision_p)
    seed = dict(storeys=vm["storeys"], podium_coverage=vision_p["podium_coverage"], homes=vm["homes"],
                open_space=vm["open_space"])
    S0 = vm["storeys"]
    t_share = vision_p["tower_storeys"] / S0
    cov_ratio = vision_p["tower_coverage"] / vision_p["podium_coverage"]
    best, n, feasible = None, 0, 0
    blockers = {k: 0 for k in walk}
    for s in range(2, int(S0) + 7):
        ts = round(s * t_share)
        ps = s - ts
        for ci in range(9):
            pc = round(0.30 + 0.05 * ci, 2)
            for aff in range(0, 51, 5):
                p = dict(vision_p, podium_storeys=ps, tower_storeys=ts, podium_coverage=pc,
                         tower_coverage=pc * cov_ratio, affordable_hr_pct=aff)
                u, r = utilities(p, seed, median)
                n += 1
                keys = [k for k in walk if include_res or k != "res"]
                if all(u[k] > walk[k] for k in keys):
                    feasible += 1
                    prod = 1.0
                    for k in keys:
                        prod *= (u[k] - walk[k])
                    if best is None or prod > best[0]:
                        best = (prod, dict(storeys=s, podium_storeys=ps, tower_storeys=ts, podium_coverage=pc,
                                           affordable=aff, homes=round(r["homes"], 1), surplus=round(r["surplus"]),
                                           U={k: round(v, 3) for k, v in u.items()}))
                else:
                    for k in keys:
                        if u[k] <= walk[k]:
                            blockers[k] += 1
    return dict(n=n, feasible=feasible, best=best, blockers=blockers)
