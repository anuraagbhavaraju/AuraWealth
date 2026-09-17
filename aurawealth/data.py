import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "wealth.db"

def _con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute("create table if not exists clients (id text primary key,name text,income real,cash real,investments real,emergency real,balance real,rate real,years int,payment real,goal text,target real,goal_month text,saved real,saving real,housing real,living real,commitments real)")
    c.execute("create table if not exists subscriptions (client_id text,service text,amount real,month text)")
    if not c.execute("select count(*) from clients").fetchone()[0]:
        rows=[("client_001","Alex Tan",8500,22000,128000,15000,480000,3.2,22,2500,"December holiday",6000,"2026-12",1800,700,3100,1900,900),("client_002","Maya Lim",7200,18000,76000,12000,320000,3,18,1900,"Education fund",10000,"2027-06",4200,500,2600,1600,800)]
        c.executemany("insert into clients values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",rows)
        for cid,*_ in rows:
            for m in range(4,10):
                for s,a,b in [("Netflix",20,22),("Spotify",12,12),("Adobe",25,35)]: c.execute("insert into subscriptions values (?,?,?,?)",(cid,s,a if m<7 else b,f"2026-{m:02}"))
        c.commit()
    return c

def client_options():
    c=_con(); r=[(x["id"],x["name"]) for x in c.execute("select id,name from clients")]; c.close(); return r

def load_client_data(client_id="client_001"):
    c=_con(); r=c.execute("select * from clients where id=?",(client_id,)).fetchone()
    if not r: raise ValueError("Unknown client scope")
    subs=[dict(x) for x in c.execute("select service,amount,month from subscriptions where client_id=?",(client_id,))]; c.close()
    return {"client":{"id":r["id"],"name":r["name"],"monthly_income":r["income"],"cash_balance":r["cash"],"investment_balance":r["investments"],"emergency_fund_target":r["emergency"]},"mortgage":{"outstanding_balance":r["balance"],"interest_rate_percent":r["rate"],"remaining_years":r["years"],"monthly_payment":r["payment"]},"goal":{"name":r["goal"],"target_amount":r["target"],"target_month":r["goal_month"],"saved_amount":r["saved"],"monthly_saving":r["saving"]},"monthly_expenses":{"housing_and_bills":r["housing"],"living_costs":r["living"],"other_commitments":r["commitments"]},"subscriptions":subs}
