"""Script para descargar los Reportes Financieros de FibraNova (FNOVA)."""

import os
import time
import urllib.request

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "fnova")

FILES = [
    ("2026T1", "https://fibranova.s3.us-east-1.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2026-1T26.pdf"),
    ("2025T4", "https://fibranova.s3.us-east-1.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2025-4T25.pdf"),
    ("2025T3", "https://investorcloud.s3.us-east-1.amazonaws.com/FNOVA/InformacionFinanciera/ReportesTrimestrales/2025-3T25.pdf"),
    ("2025T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2025-2T25.pdf"),
    ("2025T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2025-1T25.pdf"),
    ("2024T4", "https://fibranova.s3.us-east-1.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2024-4T24.pdf"),
    ("2024T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2024-3T24-.pdf"),
    ("2024T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2024-2T24.pdf"),
    ("2024T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2024-1T24.pdf"),
    ("2023T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2023-4T23-D.pdf"),
    ("2023T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2023-3T23.pdf"),
    ("2023T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2023-2T2023.pdf"),
    ("2023T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2023-1T23.pdf"),
    ("2022T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2022-4T22.pdf"),
    ("2022T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2022-3T22.pdf"),
    ("2022T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2022-2T22.pdf"),
    ("2022T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2022-1T22.pdf"),
    ("2021T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2021-4T21.pdf"),
    ("2021T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2021-3T21.pdf"),
    ("2021T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2021-2T21.pdf"),
    ("2021T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2021-1T21.pdf"),
    ("2020T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2020-4T20.pdf"),
    ("2020T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2020-3T20.pdf"),
    ("2020T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2020-2T20.pdf"),
    ("2020T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2020-1T20.pdf"),
    ("2019T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2019-4T19.pdf"),
    ("2019T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2019-3T19.pdf"),
    ("2019T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2019-2T19.pdf"),
    ("2019T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2019-1T19.pdf"),
    ("2018T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2018-4T18.pdf"),
    ("2018T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2018-3T18.pdf"),
    ("2018T2", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2018-2T18.pdf"),
    ("2018T1", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2018-1T18.pdf"),
    ("2017T4", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2017-4T17.pdf"),
    ("2017T3", "https://fibranova.s3.amazonaws.com/fnova/InformacionFinanciera/ReportesTrimestrales/2017-3T17.pdf"),
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
