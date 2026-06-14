from pydantic import BaseModel


class InflationRecord(BaseModel):
    """Annual Mexican inflation snapshot (INPC, INEGI/Banxico).

    Attributes:
        year: Calendar year of the measurement.
        annual_inflation: Annual inflation rate as a decimal (e.g. 0.0421 = 4.21 %).
    """

    year: int
    annual_inflation: float
