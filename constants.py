BT = [f"BT{i}" for i in range(1, 27)]
EX = [f"EX{i}" for i in range(1, 13)]
ST = [f"ST{i}" for i in range(1, 26)]
OTHERS = ['LM','RB1','P','AD1']
ALL_SETS = BT + EX + ST + OTHERS

"""There are no other typers of sets in the Digimon TCG as of now."""
ALLOWED_SETS = set(ALL_SETS)
"""These are all relevant rarities in Digimon TCG. Alternate arts are not taken into account"""
ALLOWED_RARITIES = set({'C', 'U', 'R', 'UR', 'SEC', 'P', 'SR'})
"""Format for use in SQL statements"""
ALLOWED_RARITIES_SQL = "'C', 'U', 'R', 'UR', 'SEC', 'P', 'SR'"

CARD_SET_ORDER_EXPR = (
    "CASE "
    "CASE WHEN instr(p.card_number, '-') > 0 "
    "THEN substr(p.card_number, 1, instr(p.card_number, '-') - 1) "
    "ELSE p.card_number END "
    + " ".join(
        f"WHEN '{name}' THEN {i}"
        for i, name in enumerate(ALL_SETS)
    )
    + " ELSE 999 END"
)

CARD_SUFFIX_ORDER_EXPR = (
    "CASE WHEN instr(p.card_number, '-') > 0 "
    "THEN CAST(substr(p.card_number, "
    "instr(p.card_number, '-') + 1) AS INTEGER) "
    "ELSE NULL END"
)

CARD_ORDER_SQL = (
    f"{CARD_SET_ORDER_EXPR}, "
    f"{CARD_SUFFIX_ORDER_EXPR}, "
    "p.card_number COLLATE NOCASE"
)