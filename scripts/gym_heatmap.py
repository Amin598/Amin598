# scripts/gym_heatmap.py
import os, csv, io, requests
from datetime import date, datetime, timedelta

# ---------- Settings ----------
CELL = 10          # Zellgröße
GAP = 2            # Abstand zwischen Zellen
PAD = 16           # Innenabstand im Container
LEFT_LABEL_W = 24  # Platz für Wochentagslabels links
TOP_LABEL_H = 18   # Platz für Monatslabels oben

COLOR_EMPTY = "#2d333b"   # dunkelgrau (leer)
COLOR_FILL  = "#0a84ff"   # blau (Gym)
COLOR_TEXT  = "#8b949e"   # dezente Label-Farbe
COLOR_FRAME = "#30363d"   # Rahmenfarbe
RADIUS = 3                # Eckenradius der Zellen/Container
FONT_FAMILY = "ui-sans-serif, -apple-system, Segoe UI, Roboto, Helvetica, Arial"

CSV_URL = os.environ.get("SHEET_CSV_URL")
if not CSV_URL:
    raise SystemExit("SHEET_CSV_URL env var missing")

# ---------- CSV holen ----------
r = requests.get(CSV_URL, timeout=30)
r.raise_for_status()
reader = csv.DictReader(io.StringIO(r.text))

def parse_date(s: str):
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

gym_dates = set()
for row in reader:
    d = parse_date(row.get("Date", "") or "")
    v = (row.get("Gym", "") or "").strip().lower()
    if d and v == "yes":
        gym_dates.add(d)

# ---------- Zeitraum (letzte 52/53 Wochen) ----------
today = date.today()
start = today - timedelta(days=364)
# Auf Sonntag ausrichten, damit Reihenfolge wie bei GitHub funktioniert
while start.weekday() != 6:  # 6 = Sonntag
    start -= timedelta(days=1)

days_total = (today - start).days + 1
cols = (days_total + 6) // 7  # Wochen

# ---------- Maße ----------
grid_w = cols * (CELL + GAP) - GAP
grid_h = 7 * (CELL + GAP) - GAP

width  = LEFT_LABEL_W + PAD + grid_w + PAD
height = TOP_LABEL_H + PAD + grid_h + PAD

def rect(x, y, w, h, fill, rx=RADIUS, ry=RADIUS, stroke=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" rx="{rx}" ry="{ry}"'
    if stroke:
        s += f' stroke="{stroke}"'
    s += '/>'
    return s

def text(x, y, content, size=10, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT_FAMILY}" font-size="{size}" '
            f'fill="{COLOR_TEXT}" text-anchor="{anchor}">{content}</text>')

# ---------- SVG aufbauen ----------
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']

# Container-Rahmen
svg.append(rect(0.5, 0.5, width-1, height-1, "none", rx=8, ry=8, stroke=COLOR_FRAME))

# Wochentagslabels links (Mon, Wed, Fri)
left_x = PAD
base_y = TOP_LABEL_H + PAD
row_y = lambda r: base_y + r*(CELL+GAP) + CELL - 2  # leichte optische Korrektur

svg.append(text(LEFT_LABEL_W - 6, row_y(1), "Mon", size=9, anchor="end"))
svg.append(text(LEFT_LABEL_W - 6, row_y(3), "Wed", size=9, anchor="end"))
svg.append(text(LEFT_LABEL_W - 6, row_y(5), "Fri", size=9, anchor="end"))

# Monatslabels oben – immer beim ersten Tag eines Monats (oder erster sichtbarer Spalte)
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
cur = start
last_month = None
for i in range(cols):
    # Datum des Sonntags (oberste Zeile) der jeweiligen Woche
    week_date = cur + timedelta(days=i*7)
    m = week_date.month
    # Label wenn Monat wechselt oder erste Spalte
    if i == 0 or m != last_month:
        x = LEFT_LABEL_W + PAD + i*(CELL+GAP)
        svg.append(text(x, PAD + 11, month_names[m-1], size=10, anchor="start"))
        last_month = m

# Zellen
cur_day = start
for i in range(days_total):
    col = i // 7
    row = (cur_day.weekday() + 1) % 7  # Sonntag oben
    x = LEFT_LABEL_W + PAD + col*(CELL+GAP)
    y = TOP_LABEL_H + PAD + row*(CELL+GAP)
    color = COLOR_FILL if cur_day in gym_dates else COLOR_EMPTY
    svg.append(rect(x, y, CELL, CELL, color))
    cur_day += timedelta(days=1)

svg.append("</svg>")
open("gym-graph.svg","w",encoding="utf-8").write("\n".join(svg))
print("gym-graph.svg written")
