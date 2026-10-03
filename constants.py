BT = [f"BT{i}" for i in range(1, 27)]
EX = [f"EX{i}" for i in range(1, 13)]
ST = [f"ST{i}" for i in range(1, 26)]
OTHERS = ['LM','RB1','P','AD1']
ALL_SETS = BT + EX + ST + OTHERS
ALLOWED_SETS = set(ALL_SETS)

ALLOWED_RARITIES = set({'C', 'U', 'R', 'UR', 'SEC', 'P', 'SR'})