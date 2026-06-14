from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class PaymentFrequency(StrEnum):
    """Distribution payment frequency for a FIBRA.

    Attributes:
        MONTHLY: Distributions are paid once a month.
        QUARTERLY: Distributions are paid once per quarter.
    """

    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"


class Sector(StrEnum):
    """Real-estate sector classification for a FIBRA's portfolio.

    Attributes:
        INDUSTRIAL: Industrial and logistics properties.
        COMERCIAL: Retail and shopping centre properties.
        OFICINAS: Office properties.
        HOTELERO: Hotel and hospitality properties.
        HIPOTECARIO: Mortgage and housing finance.
        EDUCATIVO: Educational facility properties.
        ALMACENAJE: Storage and warehouse properties.
    """

    INDUSTRIAL = "Industrial"
    COMERCIAL = "Comercial"
    OFICINAS = "Oficinas"
    HOTELERO = "Hotelero"
    HIPOTECARIO = "Hipotecario"
    EDUCATIVO = "Educativo"
    ALMACENAJE = "Almacenaje"


class SectorExposure(BaseModel):
    """A single sector allocation entry in a FIBRA's portfolio breakdown.

    Attributes:
        sector: The real-estate sector.
        weight: Fraction of the portfolio allocated to this sector (0–1).
    """

    sector: Sector
    weight: float


class Fibra(BaseModel):
    """Static catalog entry for a FIBRA listed on the BMV.

    Attributes:
        ticker: BMV ticker (e.g. "FMTY14").
        name: Full commercial name of the FIBRA (e.g. "Fibra Mty").
        payment_frequency: How often distributions are paid.
        sector_exposure: Breakdown of the portfolio by real-estate sector.
        tenant_concentration_basis: Income base used by this FIBRA when reporting
            tenant concentration (e.g. "ingresos_totales", "renta_fija",
            "renta_neta_efectiva"). Null if not applicable.
    """

    ticker: str
    name: str
    payment_frequency: PaymentFrequency
    sector_exposure: list[SectorExposure]
    tenant_concentration_basis: Optional[str] = None
