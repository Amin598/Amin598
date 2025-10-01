import os, csv, io, requests
from datetime import date, datetime, timedelta

CSV_URL = os.environ.get("SHEET_CSV_URL")
if not CSV_URL:
    raise SystemExit("SHEET_CSV_URL env var missing")

r = requests.get(CSV_URL, timeout=30)
r.raise_for_status()

reader = csv.DictReader(io.StringIO(r.text))
gym_dates = set()

def parse_date(s):
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try: return datetime.strptime(s, fmt).date()
        except ValueError: pass
    return None

for row in reader:
    d = parse_date(row.get("Date",""))
    v = (row.get("Gym","") or "").strip().lower()
    if d and v == "yes":
        gym_dates.add(d)

today = date.today()
start = today - timedelta(days=364)
while start.weekday() != 6:  # auf Sonntag ausrichten
    start -= timedelta(days=1)

days_total = (today - start).days + 1
cols = (days_total + 6)//7

cell, gap, left, top = 10, 2, 20, 20
width  = left + cols*(cell+gap) + 20
height = top  + 7*(cell+gap)   + 20
empty_color, fill_color = "#ebedf0", "#0a84ff"

def rect(x,y,w,h,fill): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="2" ry="2"/>'

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
cur = start
for i in range(days_total):
    col = i//7
    row = (cur.weekday()+1)%7  # Sonntag oben
    x = left + col*(cell+gap); y = top + row*(cell+gap)
    color = fill_color if cur in gym_dates else empty_color
    svg.append(rect(x,y,cell,cell,color))
    cur += timedelta(days=1)
svg.append("</svg>")
open("gym-graph.svg","w",encoding="utf-8").write("\n".join(svg))
