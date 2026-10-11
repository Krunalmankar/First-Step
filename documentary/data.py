"""Every figure shown on screen, with its source. See SOURCES.md for links and verification status."""

AS_OF = "Figures verified as of 11 October 2026 · Fiscal year 2026 ran 1 Oct 2025 – 30 Sep 2026"

SRC_DTP = "Source: US Treasury, Debt to the Penny (total public debt outstanding, 8 Oct 2026)"
SRC_MBR = "Source: CBO, Monthly Budget Review: September 2026 (8 Oct 2026)"
SRC_BEO = "Source: CBO, The Budget and Economic Outlook: 2026 to 2036 (Feb 2026)"
SRC_COFER = "Source: IMF, COFER (currency composition of official FX reserves), Q2 2026"
SRC_RATINGS = "Source: S&P Global Ratings (Aug 2011), Fitch Ratings (Aug 2023), Moody's Ratings (May 2025)"
SRC_YIELD = "Source: US Treasury constant-maturity yields via FRED (DGS30); TreasuryDirect auction results"
SRC_BOE = "Source: Bank of England, letter from Deputy Governor Jon Cunliffe to the Treasury Committee (Oct 2022)"
SRC_NTUF = "Source: US Treasury; National Taxpayers Union Foundation, Projecting the Debt Limit"

DEBT_TOTAL_T = 40.31            # $ trillion, 8 Oct 2026
DEBT_MILESTONES = [("$38T", "Oct 2025"), ("$39T", "Mar 2026"), ("$40T", "Aug 2026")]
DEBT_LIMIT_T = 41.104           # set 4 July 2025

# FY2026 ($ billions) — CBO Monthly Budget Review, Sept 2026
OUTLAYS = [("Social Security", 1654), ("Net interest", 1143), ("Medicare", 1069), ("Defense", 916)]
SPENT_T, COLLECTED_T = 7.4, 5.4
DEFICIT_B = 1993
INTEREST_PER_SEC = 1143e9 / (365 * 86400)        # ≈ $36,245 per second, FY2026 average
DEFICIT_PER_DAY_B = DEFICIT_B / 365               # ≈ $5.5B per day
INTEREST_JUMP_B = 115
REVENUE_RISE_B = 169
PER_PERSON = 115_000

NET_INTEREST_2036_T = 2.1       # CBO projection
DEFICIT_2036_T = 3.1            # CBO projection
DEBT_GDP_2026, DEBT_GDP_2036, DEBT_GDP_1946 = 101, 120, 106   # debt held by the public, % of GDP

# 30-year Treasury yield, annual averages (%). Approximate values from FRED DGS30 —
# re-check against the series before publishing (see SOURCES.md, "values to re-verify").
YIELD_30Y = [(2007, 4.84), (2008, 4.28), (2009, 4.08), (2010, 4.25), (2011, 3.91), (2012, 2.92), (2013, 3.45),
             (2014, 3.34), (2015, 2.84), (2016, 2.60), (2017, 2.90), (2018, 3.11), (2019, 2.58), (2020, 1.56),
             (2021, 2.06), (2022, 3.11), (2023, 4.09), (2024, 4.41), (2025, 4.81)]
YIELD_AUG26_CLOSE, YIELD_AUCTION = 5.31, 5.22

# US dollar share of allocated FX reserves (%), IMF COFER, approximate year-end values; Q2 2026 = 56.7
USD_SHARE = [(2000, 71.1), (2002, 66.5), (2004, 65.5), (2006, 65.5), (2008, 63.8), (2010, 62.2), (2012, 61.5),
             (2014, 65.1), (2016, 65.4), (2018, 61.7), (2020, 59.0), (2022, 58.4), (2024, 57.8), (2026.5, 56.7)]
RESERVES_Q2_2026 = [("US dollar", 56.7), ("Euro", 20.6), ("All others", 22.7)]

# Debt held by the public, % of GDP. History approximate (CBO historical data, fiscal years);
# 2026 / 2030 / 2036 are the CBO anchor points used in the script.
DEBT_GDP_HIST = [(1940, 44), (1943, 70), (1946, 106), (1950, 78), (1955, 56), (1960, 44), (1965, 37), (1970, 27),
                 (1974, 23), (1980, 25), (1985, 35), (1990, 41), (1995, 48), (2000, 34), (2007, 35), (2010, 61),
                 (2015, 72), (2019, 79), (2020, 99), (2022, 95), (2024, 98), (2026, 101)]
DEBT_GDP_PROJ = [(2026, 101), (2030, 107), (2036, 120)]


# Rome: silver content of the main silver coin (approximate numismatic estimates; see SOURCES.md)
SRC_ROME = ("Source: numismatic estimates (K. Harl, Coinage in the Roman Economy, 1996; D. Walker, "
            "The Metrology of the Roman Silver Coinage, 1976-78) · approximate")
ROME_SILVER = [("c. 14 AD", "Augustus", 95), ("c. 200 AD", "Septimius Severus", 50), ("c. 265 AD", "Gallienus", 5)]


def mortgage_payment(principal, annual_rate, years=30):
    """Standard fixed-rate amortisation: monthly payment."""
    r, n = annual_rate / 12, years * 12
    return principal * r / (1 - (1 + r) ** -n)


MORTGAGE = (400_000, 0.06, 0.07)        # illustrative: $400,000, 30-year fixed, 6% vs 7%
