"""Reemplaza los reportes de FIBRA Prologis (2014T2–2020T4) por versiones en inglés.

Los reportes en inglés contienen la información suplementaria que falta
en los reportes en español descargados anteriormente.
"""

import os
import time
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "fibrapl")

BASE = "https://d1io3yog0oux5.cloudfront.net/_173bf848f8ba48da71b026266b5e2efb/fibraprologis/db/735"

FILES = [
    ("2020T4", f"{BASE}/7556/file/FIBRAPL_4Q20_Financial+Statements_English.pdf"),
    ("2020T3", f"{BASE}/7494/file/FIBRAPL_Financial+Report_3Q20_English.pdf"),
    ("2020T2", f"{BASE}/7437/file/Financial+Release.pdf"),
    ("2020T1", f"{BASE}/7279/file/first-quarter-2020-financial-report-en.pdf"),
    ("2019T4", f"{BASE}/7278/file/financial-report-4q-19.pdf"),
    ("2019T3", f"{BASE}/6288/file/third-quarter-2019-financial-report.pdf"),
    ("2019T2", f"{BASE}/6287/file/second-quarter-2019-financial-report.pdf"),
    ("2019T1", f"{BASE}/6286/file/first-quarter-2019-financial-report-v2.pdf"),
    ("2018T4", f"{BASE}/6285/file/en-fourth-quarter-2018-financial-report.pdf"),
    ("2018T3", f"{BASE}/6284/file/third-quarter-2018-financial-report.pdf"),
    ("2018T2", f"{BASE}/6283/file/second-quarter-2018-financial-report.pdf"),
    ("2018T1", f"{BASE}/6282/file/first-quarter-2018-financial-report.pdf"),
    ("2017T4", f"{BASE}/6281/file/en-fourth-quarter-2017-financial-report.pdf"),
    ("2017T3", f"{BASE}/6280/file/third-quarter-2017-financial-report-en.pdf"),
    ("2017T2", f"{BASE}/6279/file/second-quarter-2017-financial-report-en.pdf"),
    ("2017T1", f"{BASE}/6278/file/first-quarter-2017-financial-report-en.pdf"),
    ("2016T4", f"{BASE}/6277/file/fourth-quarter-2016-financial-report-q4-2016.pdf"),
    ("2016T3", f"{BASE}/6276/file/third-quarter-2016-financial-report-q3-2016.pdf"),
    ("2016T2", f"{BASE}/6275/file/financial-report-q2-2016-english.pdf"),
    ("2016T1", f"{BASE}/6274/file/financial-report-q1-2016-english.pdf"),
    ("2015T4", f"{BASE}/6272/file/fourth-quarter-2015-financial-report-v3.pdf"),
    ("2015T3", f"{BASE}/6270/file/third-quarter-2015-financial-report-22-10-2015.pdf"),
    ("2015T2", f"{BASE}/6268/file/second-quarter-2015-financial-report-en-v1.pdf"),
    ("2015T1", f"{BASE}/6266/file/first-quarter-2015-financial-report.pdf"),
    ("2014T4", f"{BASE}/6263/file/financial-report-4Q2014.pdf"),
    ("2014T3", f"{BASE}/6261/file/q3-2014-fibra-prologis-report-english.pdf"),
    ("2014T2", f"{BASE}/6260/file/2q14-fibra-prologis-reporte-fianl-english.pdf"),
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
