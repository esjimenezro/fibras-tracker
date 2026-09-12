"""Script para descargar los Reportes Financieros de Fibra MTY (pre-2021)."""

import os
import time
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "fmty")

BASE = "https://cdn.investorcloud.net/fibramty/InformacionFinanciera/ReportesTrimestrales/Reportes"

FILES = [
    ("2020T4", f"{BASE}/2020-4T20-Reporte-.pdf"),
    ("2020T3", f"{BASE}/2020-3T20-Reporte.pdf"),
    ("2020T2", f"{BASE}/2020-2T20-Reporte-.pdf"),
    ("2020T1", f"{BASE}/2020-1T20-Reporte.pdf"),
    ("2019T4", f"{BASE}/2019-4T19-Reporte-En.pdf"),
    ("2019T3", f"{BASE}/2019-3T19-Reporte.pdf"),
    ("2019T2", f"{BASE}/2019-2T19-Reporte.pdf"),
    ("2019T1", f"{BASE}/2019-1T19-Reporte.pdf"),
    ("2018T4", f"{BASE}/2018-4T18-Reporte.pdf"),
    ("2018T3", f"{BASE}/2018-3T18-Reporte.pdf"),
    ("2018T2", f"{BASE}/2018-2T18-Reporte-En-vf.pdf"),
    ("2018T1", f"{BASE}/2018-1T18-Reporte.pdf"),
    ("2017T4", f"{BASE}/2017-4T17-Reporte.pdf"),
    ("2017T3", f"{BASE}/2017-3T17-Reporte.pdf"),
    ("2017T2", f"{BASE}/2017-2T17-Reporte.pdf"),
    ("2017T1", f"{BASE}/2017-1T17-Reporte.pdf"),
    ("2016T4", f"{BASE}/2016-4T16-Reporte.pdf"),
    ("2016T3", f"{BASE}/2016-3T16-Reporte.pdf"),
    ("2016T2", f"{BASE}/2016-2T16-Reporte.pdf"),
    ("2016T1", f"{BASE}/2016-1T16-Reporte.pdf"),
    ("2015T4", f"{BASE}/2015-4T15-Reporte.pdf"),
    ("2015T3", f"{BASE}/2015-3T15-Reporte.pdf"),
    ("2015T2", f"{BASE}/2015-2T15-Reporte.pdf"),
    ("2015T1", f"{BASE}/2015-1T15-Reporte.pdf"),
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ok, errors = 0, []

    for name, url in FILES:
        dest = os.path.join(OUTPUT_DIR, f"{name}.pdf")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            print(f"OK  {name} ({len(data):,} bytes)")
            ok += 1
        except Exception as e:
            print(f"ERR {name}: {e}")
            errors.append(name)
        time.sleep(0.3)

    print(f"\nResultado: {ok} OK, {len(errors)} errores")
    if errors:
        print("Fallaron:", ", ".join(errors))


if __name__ == "__main__":
    main()
