# The 75.0% vs 56.3% roof "room vs home" check run by Claude at 10:59 on 26 Sep 2026.
# Exploratory keyword classes, NOT validated categories (see the ChatGPT audit in mvp_chatgpt/Approval-rate-audit.md).
import sys, duckdb
P = sys.argv[1] if len(sys.argv) > 1 else "data/foundations.parquet"
con = duckdb.connect()
con.execute(f"""create view r as select *, lower(description) d,
 case when status in ('Permitted','Conditions') then 1 when status='Rejected' then 0 end ok
 from '{P}'
 where regexp_matches(lower(description),'mansard|hip.to.gable|dormer|loft|additional stor|additional floor|upward extension|roof extension')
   and app_type='Full' and not regexp_matches(lower(description),'certificate|lawful')""")
con.execute("""create view c as select *, case
  when regexp_matches(d,'into (\\d+ |two |three |four )?(self.contained )?flats|self.contained') then 'B_conversion'
  when regexp_matches(d,'(new|creation of|additional) (\\d+ )?(flat|dwelling|unit)|\\d+ ?x ?(flat|dwelling)') then 'A_new_home'
  else 'room_only' end cls from r""")
print(con.execute("select cls, count(*) n, count(ok) decided, round(avg(ok),3) approval, round(median(days_to_decision)) med_days from c group by 1 order by 1").fetchdf().to_string())
print(con.execute("select case when cls='room_only' then 'room' else 'home' end k, count(ok) decided, round(avg(ok),3) approval from c group by 1").fetchdf().to_string())
