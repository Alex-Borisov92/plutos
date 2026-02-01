"""
Preflop ranges data module.

Contains all preflop opening and defense ranges for 50-100bb with ante.
Also includes ICM push/fold ranges for short stacks (1-10bb).

Position naming convention:
- UTG, UTG+1, UTG+2, LJ, HJ, CO, BTN, SB, BB (9-max)

Hand notation:
- Pairs: "AA", "KK", "22"
- Suited: "AKs", "T9s"
- Offsuit: "AKo", "T9o"
"""
from typing import Dict, Set, FrozenSet


# Type aliases for clarity
HandSet = FrozenSet[str]
PositionRanges = Dict[str, HandSet]
DefenseRanges = Dict[str, Dict[str, HandSet]]  # {action: set of hands}
NestedDefenseRanges = Dict[str, Dict[str, DefenseRanges]]  # [def_pos][open_pos][action]


# -----------------------------------------------------------------------------
# Opening ranges (RFI) - 50-100bb with ante
# -----------------------------------------------------------------------------

OPEN_RANGES: Dict[str, HandSet] = {
    "UTG": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A5s",
        "KQs", "KJs", "KTs",
        "QJs", "QTs",
        "JTs",
        "T9s", "98s",
        "AKo", "AQo",
    }),

    "UTG+1": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s",
        "KQs", "KJs", "KTs", "K9s",
        "QJs", "QTs", "Q9s",
        "JTs", "J9s",
        "T9s", "98s", "87s",
        "AKo", "AQo", "AJo", "KQo",
    }),

    "UTG+2": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s",
        "QJs", "QTs", "Q9s",
        "JTs", "J9s",
        "T9s", "98s", "87s", "76s",
        "AKo", "AQo", "AJo", "KQo",
    }),

    "LJ": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s",
        "QJs", "QTs", "Q9s",
        "JTs", "J9s",
        "T9s", "98s", "87s", "76s", "65s",
        "AKo", "AQo", "AJo", "ATo", "KJo", "KQo",
    }),

    "HJ": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s", "K8s",
        "QJs", "QTs", "Q9s",
        "JTs", "J9s",
        "T9s", "T8s",
        "98s", "97s",
        "87s", "76s", "65s", "54s",
        "AKo", "AQo", "AJo", "ATo",
        "KQo", "KJo", "QJo",
    }),

    "CO": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
        "QJs", "QTs", "Q9s", "Q8s",
        "JTs", "J9s", "J8s",
        "T9s", "T8s",
        "98s", "97s",
        "87s", "86s", "76s", "75s", "65s", "64s", "54s", "43s",
        "AKo", "AQo", "AJo", "ATo", "A9o",
        "KQo", "KJo", "KTo",
        "QJo", "QTo",
        "JTo",
    }),

    "BTN": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
        "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
        "JTs", "J9s", "J8s", "J7s", "J6s",
        "T9s", "T8s", "T7s", "T6s",
        "98s", "97s", "96s",
        "87s", "86s", "85s",
        "76s", "75s", "74s",
        "65s", "64s",
        "54s", "53s",
        "43s",
        "32s",
        "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
        "KQo", "KJo", "KTo", "K9o", "K8o", "K7o",
        "QJo", "QTo", "Q9o", "Q8o",
        "JTo", "J9o", "J8o",
        "T9o", "T8o",
        "98o", "97o",
        "87o",
        "76o",
    }),

    "SB": frozenset({
        "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
        "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
        "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
        "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
        "T9s", "T8s", "T7s", "T6s", "T5s", "T4s",
        "98s", "97s", "96s",
        "87s", "86s", "85s",
        "76s", "75s", "74s",
        "65s", "64s", "63s",
        "54s", "53s",
        "43s",
        "32s",
        "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
        "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o", "K4o", "K3o", "K2o",
        "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o", "Q3o", "Q2o",
        "J9o", "J8o", "J7o", "J6o",
        "T9o", "T8o", "T7o", "T6o",
        "98o", "97o", "96o",
        "87o", "86o",
        "76o",
        "65o",
    }),
}


# -----------------------------------------------------------------------------
# Defense vs Open (facing open raise) - 50-100bb with ante
# Structure: DEFENSE_VS_OPEN[defender_pos][opener_pos] = {"3bet": set, "call": set, "3bet_bluff": set}
# -----------------------------------------------------------------------------

DEFENSE_VS_OPEN: NestedDefenseRanges = {
    "UTG+1": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "AQs", "AJs", "KQs", "QJs", "JTs"}),
            "3bet_bluff": frozenset({"ATs", "KJs", "AQo"}),
        },
    },
    "UTG+2": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "AQs", "AJs", "KQs", "QJs", "JTs"}),
            "3bet_bluff": frozenset({"ATs", "KJs", "AQo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "AQs", "AJs", "KQs", "QJs", "JTs"}),
            "3bet_bluff": frozenset({"ATs", "KJs", "AQo"}),
        },
    },
    "LJ": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "AQs", "AJs", "KQs", "QJs", "JTs"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "KJs", "AQo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "AQs", "AJs", "KQs", "QJs", "JTs"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "KJs", "AQo"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "66", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "KJs", "AQo", "98s"}),
        },
    },
    "HJ": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "KJs", "AQo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "66", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "KJs", "AQo"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"JJ", "TT", "99", "88", "77", "66", "55", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s", "98s"}),
            "3bet_bluff": frozenset({"ATs", "A5s", "A4s", "A3s", "KJs", "AQo", "87s", "76s"}),
        },
        "LJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55",
                "AQs", "AJs", "ATs",
                "KQs", "KJs",
                "QJs",
                "JTs", "T9s", "98s", "87s",
            }),
            "3bet_bluff": frozenset({"A5s", "A4s", "A3s", "A2s", "AJo", "KQo", "76s", "65s"}),
        },
    },
    "CO": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88",
                "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "QJs", "QTs",
                "JTs", "T9s", "98s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88",
                "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "QJs", "QTs",
                "JTs", "T9s", "98s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77",
                "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "QJs", "QTs",
                "JTs", "T9s", "98s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo"}),
        },
        "LJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55",
                "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo", "76s"}),
        },
        "HJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s", "76s", "75s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo"}),
        },
    },
    "BTN": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo"}),
        },
        "LJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s", "J8s",
                "T9s", "T8s",
                "98s", "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo", "QJo"}),
        },
        "HJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s", "J8s",
                "T9s", "T8s",
                "98s", "97s",
                "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo", "QJo"}),
        },
        "CO": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs", "AJs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "ATs", "A9s", "A8s", "A7s", "A6s",
                "KQs", "KJs", "KTs", "K9s",
                "QJs", "QTs", "Q9s", "Q8s",
                "JTs", "J9s", "J8s",
                "T9s", "T8s",
                "98s", "97s",
                "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo", "QJo"}),
        },
    },
    "SB": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({
                "JJ", "TT", "99",
                "AQs", "AJs", "ATs", "A9s",
                "KQs", "KJs",
                "QJs",
                "JTs",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({
                "JJ", "TT", "99",
                "AQs", "AJs", "ATs", "A9s",
                "KQs", "KJs",
                "QJs",
                "JTs",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({
                "JJ", "TT", "99",
                "AQs", "AJs", "ATs", "A9s",
                "KQs", "KJs",
                "QJs",
                "JTs",
                "T9s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "98s"}),
        },
        "LJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88",
                "AJs", "ATs", "A9s",
                "KQs", "KJs",
                "QJs",
                "JTs",
                "T9s", "98s", "87s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo"}),
        },
        "HJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55",
                "AJs", "ATs", "A9s", "A8s",
                "KQs", "KJs", "KTs",
                "QJs", "QTs",
                "JTs", "J9s",
                "T9s", "T8s",
                "98s", "87s", "76s",
            }),
            "3bet_bluff": frozenset({"A5s", "AQo", "AJo", "KQo", "QJo"}),
        },
        "CO": {
            "3bet": frozenset({
                "AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "KQs", "KQo",
            }),
            "call": frozenset(),
            "3bet_bluff": frozenset({
                "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s",
                "KJs", "KJo",
                "QJs", "QJo",
                "JTs",
                "T9s", "98s",
            }),
        },
        "BTN": {
            "3bet": frozenset({
                "AA", "KK", "QQ", "JJ", "TT",
                "AKs", "AQs", "AJs", "ATs",
                "KQs", "KJs",
                "AKo", "AQo", "AJo", "KQo",
            }),
            "call": frozenset(),
            "3bet_bluff": frozenset({
                "99", "88", "77", "66", "55", "44", "33", "22",
                "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
                "JTs", "J9s", "J8s", "J7s", "J6s",
                "T9s", "T8s", "T7s", "T6s",
                "98s", "97s", "96s",
                "87s", "86s", "85s",
                "76s", "75s", "74s",
                "65s", "64s",
                "54s", "53s",
                "43s",
                "32s",
                "ATo", "KJo", "QJo",
            }),
        },
    },
    "BB": {
        "UTG": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AKo", "AQo", "AJo", "ATo",
                "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s",
                "KQo",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s",
                "QJo",
                "JTs", "J9s", "J8s", "J7s",
                "T9s", "T8s", "T7s",
                "98s", "97s", "96s",
                "87s",
            }),
            "3bet_bluff": frozenset({"86s", "76s", "75s", "65s", "64s", "54s", "43s"}),
        },
        "UTG+1": {
            "3bet": frozenset({"AA", "KK", "QQ", "AKs", "AQs"}),
            "call": frozenset({
                "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AKo", "AQo", "AJo", "ATo",
                "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s",
                "KQo",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s",
                "QJo",
                "JTs", "J9s", "J8s", "J7s",
                "T9s", "T8s", "T7s",
                "98s", "97s", "96s",
                "87s",
            }),
            "3bet_bluff": frozenset({"86s", "76s", "75s", "65s", "64s", "54s", "43s"}),
        },
        "UTG+2": {
            "3bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AQs", "AKo"}),
            "call": frozenset({
                "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AQo", "AJo", "ATo",
                "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s",
                "KQo", "KJo", "KTo",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s",
                "QJo", "QTo",
                "JTs", "J9s", "J8s", "J7s", "J6s",
                "JTo",
                "T9s", "T8s", "T7s", "T6s",
                "98s", "97s", "96s",
                "87s",
            }),
            "3bet_bluff": frozenset({"86s", "85s", "76s", "75s", "74s", "65s", "64s", "54s", "53s", "43s"}),
        },
        "LJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "AKo", "KQs"}),
            "call": frozenset({
                "AQo", "AJo", "ATo",
                "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "KQo", "KJo", "KTo",
                "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                "QJo", "QTo",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s",
                "JTo",
                "JTs", "J9s", "J8s", "J7s", "J6s", "J5s",
                "T9s", "T8s", "T7s", "T6s", "T5s",
                "99", "98s", "97s", "96s", "95s",
                "88", "87s", "86s",
                "77", "76s",
                "66",
                "55",
                "44",
                "33",
                "22",
            }),
            "3bet_bluff": frozenset({"A9o", "85s", "75s", "74s", "65s", "64s", "54s", "53s", "43s"}),
        },
        "HJ": {
            "3bet": frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AQs", "AJs", "KQs", "AKo", "AQo"}),
            "call": frozenset({
                "99", "88", "77", "66", "55", "44", "33", "22",
                "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AJo", "ATo",
                "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                "KQo", "KJo", "KTo",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s",
                "QJo", "QTo",
                "JTs", "J9s", "J8s", "J7s", "J6s", "J5s",
                "JTo",
                "T9s", "T8s", "T7s", "T6s", "T5s",
                "98s", "97s", "96s", "95s",
                "87s", "86s",
            }),
            "3bet_bluff": frozenset({"A9o", "85s", "76s", "75s", "74s", "65s", "64s", "63s", "54s", "53s", "43s", "32s"}),
        },
        "CO": {
            "3bet": frozenset({
                "AA", "KK", "QQ", "JJ", "TT",
                "AKs", "AQs", "AJs", "ATs", "KQs", "KJs", "QJs",
                "AKo", "AQo", "AJo", "KQo",
            }),
            "call": frozenset({
                "99", "88", "77", "66", "55", "44", "33", "22",
                "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "ATo", "A9o", "A8o", "A5o",
                "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
                "KJo", "KTo", "K9o",
                "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s",
                "QJo", "QTo", "Q9o",
                "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s",
                "JTo", "J9o",
                "T9s", "T8s", "T7s", "T6s", "T5s", "T4s",
                "T9o",
                "98s", "97s", "96s", "95s", "94s",
                "98o",
                "87s", "86s",
            }),
            "3bet_bluff": frozenset({
                "A4o", "A3o", "85s", "84s", "76s", "75s", "74s", "73s",
                "65s", "64s", "63s", "54s", "53s", "52s", "43s", "32s",
            }),
        },
        "SB": {
            "3bet": frozenset({
                "AA", "AKo", "AKs", "AQo", "AQs", "AJo", "AJs", "ATs",
                "KK", "KQo", "KQs", "KJs", "KTs", "QQ", "QJs", "QTs",
                "JJ", "JTs", "TT", "99",
            }),
            "call": frozenset({
                "ATo", "A9o", "A9s", "A8o", "A8s", "A7o", "A7s", "A6o",
                "A6s", "A5o", "A5s", "A4o", "A4s", "A3o", "A3s", "A2s",
                "KJo", "KTo", "K9o", "K9s", "K8o", "K8s", "K7o", "K7s",
                "K6o", "K6s", "K5o", "K5s", "K4o", "K4s", "K3s", "K2s",
                "QJo", "QTo", "Q9o", "Q9s", "Q8o", "Q8s", "Q7s", "Q6s",
                "Q5s", "Q4s", "JTo", "J9o", "J9s", "J8o", "J8s", "J7o",
                "J7s", "J6s", "J5s", "J4s", "T9o", "T8o", "T7o", "T7s",
                "T6o", "T6s", "T5s", "T4s", "98o", "97o", "97s", "96o",
                "96s", "95s", "94s", "87o", "86o", "86s", "85s", "84s",
                "77", "76s", "75s", "74s", "66", "65s", "64s", "63s",
                "55", "54s", "53s", "52s", "44", "43s", "42s", "33",
                "32s", "22",
            }),
            "3bet_bluff": frozenset({
                "A2o", "K3o", "K2o", "Q4o", "Q3o", "Q2o", "J9s", "J5o",
                "T9s", "T8s", "T5o", "98s", "87s", "76o", "76s", "75o",
                "65o", "65s", "64o", "54o", "54s",
            }),
        },
    },
}


# -----------------------------------------------------------------------------
# Defense vs 3bet (we opened, villain 3bet) - 50-100bb with ante
# Structure: DEFENSE_VS_3BET[opener_pos][3bettor_pos] = {"4bet": set, "call": set, "4bet_bluff": set, "fold": set}
# -----------------------------------------------------------------------------

DEFENSE_VS_3BET: NestedDefenseRanges = {
    "UTG": {
        "UTG+1": {
            "4bet": frozenset({"AA", "AKs", "AKo", "KK"}),
            "call": frozenset({"AQs", "AJs", "KQs", "QQ", "QJs", "JJ", "JTs", "TT", "99"}),
            "4bet_bluff": frozenset({"ATs", "AQo"}),
            "fold": frozenset({"A9s", "A5s", "KJs", "KTs", "QTs", "T9s", "98s", "88", "77", "66"}),
        },
        "UTG+2": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s", "99", "98s", "88"}),
            "4bet_bluff": frozenset({"ATs", "A9s", "AQo"}),
            "fold": frozenset({"A5s", "KJs", "KTs", "QTs", "77", "66"}),
        },
        "LJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s", "99", "88"}),
            "4bet_bluff": frozenset({"ATs", "AQo"}),
            "fold": frozenset({"A5s", "KJs", "KTs", "QTs", "98s", "77", "66"}),
        },
        "HJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "AQs", "AJs", "KQs", "QJs", "JTs", "T9s", "99", "88", "77"}),
            "4bet_bluff": frozenset({"ATs", "A9s", "AQo"}),
            "fold": frozenset({"A5s", "KJs", "KTs", "QTs", "98s", "66"}),
        },
        "CO": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "AQo", "QJs", "JJ", "JTs", "TT", "T9s", "99", "88", "77"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "KTs", "QTs", "98s"}),
            "fold": frozenset({"66"}),
        },
        "BTN": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "AQo", "QJs", "JJ", "JTs", "TT", "T9s", "99", "88", "77"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "KTs", "QTs", "98s"}),
            "fold": frozenset({"66"}),
        },
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "QJs", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "KTs", "QTs"}),
            "fold": frozenset(),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "QJs", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "KTs", "QTs"}),
            "fold": frozenset(),
        },
    },
    "UTG+1": {
        "UTG+2": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "99", "88", "77", "AQs", "AJs", "KQs", "KJs", "QJs", "JTs", "T9s"}),
            "4bet_bluff": frozenset({"ATs", "A9s", "A5s", "AJo", "AQo"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "A4s", "KTs", "K9s", "KQo", "QTs", "Q9s", "J9s", "ATo", "98s", "87s", "66"}),
        },
        "LJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "99", "88", "77", "AQs", "AQo", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "T9s"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "AJo", "KTs", "QTs"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "ATo", "KQo", "K9s", "Q9s", "J9s", "98s", "87s", "66"}),
        },
        "HJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "99", "88", "77", "66", "AQs", "AQo", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "T9s", "98s", "87s"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "AJo", "KQo", "KTs", "QTs"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "K9s", "Q9s", "J9s", "ATo"}),
        },
        "CO": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "99", "88", "77", "66", "AQs", "AQo", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "T9s", "98s", "87s"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "AJo", "KQo", "KTs", "QTs"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "K9s", "Q9s", "J9s", "ATo"}),
        },
        "BTN": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "AQo", "AJo", "KQs", "KJs", "QQ", "QJs", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "KTs", "QTs", "KQo", "J9s", "ATo"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "K9s", "Q9s"}),
        },
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "AQo", "QJs", "QTs", "AJo", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "K9s", "KQo", "J9s", "ATo"}),
            "fold": frozenset({"A7s", "A6s", "Q9s"}),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "AQo", "QJs", "QTs", "AJo", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "K9s", "KQo", "J9s", "ATo"}),
            "fold": frozenset({"A7s", "A6s", "Q9s"}),
        },
    },
    "UTG+2": {
        "LJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"QQ", "JJ", "TT", "99", "88", "77", "AQs", "AQo", "AJs", "ATs", "KQs", "KJs", "QJs", "JTs", "T9s", "98s"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "A3s", "A2s", "AJo", "KQo"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "KTs", "K9s", "QTs", "Q9s", "J9s", "87s", "76s", "66", "55"}),
        },
        "HJ": {
            "4bet": frozenset({"AA", "KK", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "AQo", "QQ", "QJs", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "77", "66"}),
            "4bet_bluff": frozenset({"A9s", "A5s", "A4s", "A3s", "A2s", "KQo", "AJo", "87s"}),
            "fold": frozenset({"A8s", "A7s", "A6s", "KTs", "K9s", "QTs", "Q9s", "J9s", "76s", "55"}),
        },
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "QQ", "QJs", "QTs", "AQo", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66", "55"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "A3s", "A2s", "AJo", "KQo"}),
            "fold": frozenset({"A7s", "A6s", "K9s", "Q9s", "J9s", "76s"}),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "QQ", "QJs", "QTs", "AQo", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66", "55"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "A3s", "A2s", "AJo", "KQo"}),
            "fold": frozenset({"A7s", "A6s", "K9s", "Q9s", "J9s", "76s"}),
        },
    },
    "LJ": {
        "HJ": {
            "4bet": frozenset({"AA", "KK", "QQ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "AQo", "QJs", "QTs", "JJ", "JTs", "TT", "T9s", "99", "98s", "88", "77"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "A3s", "A2s", "AJo", "KQo"}),
            "fold": frozenset({"A7s", "A6s", "ATo", "K9s", "KJo", "Q9s", "J9s", "87s", "76s", "65s", "66", "55", "44"}),
        },
        "CO": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({"TT", "99", "88", "77", "66", "AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "T9s", "98s", "AQo"}),
            "4bet_bluff": frozenset({"A9s", "A8s", "A5s", "A4s", "A3s", "A2s", "AJo", "KQo", "87s"}),
            "fold": frozenset({"A7s", "A6s", "ATo", "KJo", "K9s", "Q9s", "J9s", "76s", "65s", "55", "44"}),
        },
        "BTN": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({"AQs", "AJs", "ATs", "KQs", "KJs", "KTs", "AQo", "QJs", "QTs", "JTs", "TT", "T9s", "99", "98s", "88", "87s", "77", "66", "55"}),
            "4bet_bluff": frozenset({"AJo", "KQo", "A9s", "A8s", "A7s", "A5s", "A4s", "A3s", "A2s", "76s"}),
            "fold": frozenset({"ATo", "KJo", "A6s", "K9s", "Q9s", "J9s", "65s", "44"}),
        },
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "AQo", "AJo",
                "KQo",
                "QJs", "QTs",
                "JTs", "J9s",
                "TT", "T9s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66",
                "55",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "ATo", "KJo"}),
            "fold": frozenset({"K9s", "Q9s", "65s", "44"}),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs",
                "AQo", "AJo",
                "KQo",
                "QJs", "QTs",
                "JTs", "J9s",
                "TT", "T9s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66",
                "55",
                "44",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "ATo", "KJo"}),
            "fold": frozenset({"K9s", "Q9s", "65s"}),
        },
    },
    "HJ": {
        "CO": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs", "K9s",
                "AQo", "AJo", "KQo",
                "QJs", "QTs", "Q9s", "Q8s",
                "JTs", "J9s", "J8s",
                "TT", "T9s",
                "99", "98s",
                "88", "87s",
                "77",
                "66",
                "55",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KJo", "ATo", "76s"}),
            "fold": frozenset({"K8s", "QJo", "97s", "65s", "54s", "44", "33", "22"}),
        },
        "BTN": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs", "K9s",
                "AQo", "AJo", "KQo",
                "QJs", "QTs", "Q9s", "Q8s",
                "JTs", "J9s", "J8s",
                "TT", "T9s", "T8s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66", "65s",
                "55", "54s",
                "44",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "K8s", "QJo", "KJo", "ATo"}),
            "fold": frozenset({"97s", "33", "22"}),
        },
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs", "K9s",
                "AQo", "AJo", "KQo",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "TT", "T9s", "T8s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66",
                "55",
                "44",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "K8s", "QJo", "ATo"}),
            "fold": frozenset({"Q8s", "97s", "65s", "54s", "33", "22"}),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs",
                "KQs", "KJs", "KTs", "K9s",
                "AQo", "AJo", "KQo",
                "QJs", "QTs", "Q9s", "Q8s",
                "JTs", "J9s",
                "TT", "T9s", "T8s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66",
                "55",
                "44",
            }),
            "4bet_bluff": frozenset({"A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "K8s", "QJo", "ATo"}),
            "fold": frozenset({"97s", "65s", "54s", "33", "22"}),
        },
    },
    "CO": {
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs", "A9s", "A5s",
                "AQo", "AJo",
                "KQs", "KJs", "KTs", "K9s",
                "KQo",
                "QJs", "QTs", "Q9s",
                "JTs", "J9s",
                "T9s",
                "99", "98s",
                "88", "87s",
                "77", "76s",
                "66",
                "55",
                "44",
            }),
            "4bet_bluff": frozenset({"A8s", "A4s", "A3s", "A2s", "KJo", "ATo", "T8s", "97s", "65s", "54s"}),
            "fold": frozenset({
                "A7s", "A6s", "K8s", "K7s", "Q8s", "QJo", "J8s", "KTo", "QTo", "JTo", "A9o",
                "86s", "75s", "64s", "43s", "33", "22",
            }),
        },
    },
    "BTN": {
        "SB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AQo", "AJo", "ATo",
                "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s",
                "JTs", "J9s", "J8s", "J7s",
                "T9s", "T8s", "T7s", "T6s",
                "99", "98s", "97s", "96s",
                "88", "87s", "86s", "85s",
                "77", "76s", "75s", "74s",
                "66", "65s", "64s",
                "55", "54s",
                "44",
                "33",
                "22",
            }),
            "4bet_bluff": frozenset({
                "K6s", "K5s", "K4s",
                "QTo", "Q9o",
                "JTo",
                "T9o",
                "A5o",
                "A8o",
                "86o",
                "75o",
                "65o",
                "54o",
                "A4o",
                "A3o",
            }),
            "fold": frozenset({
                "K3s", "K2s",
                "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
                "J6s",
                "96s", "85s", "74s",
                "A6o", "A7o",
                "KQo", "K9o", "K8o",
                "98o", "87o",
                "Q8o", "J9o",
                "T8o",
                "A2o",
                "A9o",
            }),
        },
        "BB": {
            "4bet": frozenset({"AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"}),
            "call": frozenset({
                "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
                "AQo", "AJo", "ATo",
                "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
                "QJs", "QTs", "Q9s", "Q8s", "Q7s",
                "JTs", "J9s", "J8s", "J7s",
                "T9s", "T8s", "T7s", "T6s",
                "99", "98s", "97s", "96s",
                "88", "87s", "86s", "85s",
                "77", "76s", "75s", "74s",
                "66", "65s", "64s",
                "55", "54s",
                "44",
                "33",
                "22",
            }),
            "4bet_bluff": frozenset({
                "K6s", "K5s", "K4s",
                "QTo", "Q9o",
                "JTo",
                "T9o",
                "A5o",
                "A8o",
                "86o",
                "75o",
                "65o",
                "54o",
                "A4o",
                "A3o",
            }),
            "fold": frozenset({
                "K3s", "K2s",
                "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
                "J6s",
                "96s", "85s", "74s",
                "A6o", "A7o",
                "KQo", "K9o", "K8o",
                "98o", "87o",
                "Q8o", "J9o",
                "T8o",
                "A2o",
                "A9o",
            }),
        },
    },
}


# Special case: SB vs BB (reg battle)
DEFENSE_VS_3BET_SB_VS_BB: DefenseRanges = {
    "4bet": frozenset({"AA", "KK", "QQ", "JJ", "AKs", "AKo", "AQs"}),
    "call": frozenset({
        "TT", "99", "88", "77", "66", "55", "44", "33", "22",
        "AQo",
        "AJs", "ATs", "A9s", "A8s", "A7s", "A6s",
        "KQs", "KJs", "KTs",
        "QJs", "QTs",
        "JTs",
        "T9s", "98s", "87s", "76s", "65s", "54s",
    }),
    "4bet_bluff": frozenset({"A5s", "A4s", "A3s", "A2s", "AJo", "KQo"}),
}


# -----------------------------------------------------------------------------
# ICM Push/Fold ranges - 9max
# Structure: ICM_PUSH_FOLD[stack_bucket][position] = {"push": set, "push_Xbb": set, ...}
# -----------------------------------------------------------------------------

ICM_PUSH_FOLD_1_5BB: Dict[str, Dict[str, HandSet]] = {
    "UTG": {
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
            "55", "44", "33", "22", "AKs", "AQs", "AJs", "ATs",
            "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
            "K6s", "K5s", "K4s", "K3s", "K2s", "QJs", "QTs",
            "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s",
            "Q2s", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s",
            "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s",
            "T5s", "T4s", "T3s", "T2s", "98s", "97s", "96s",
            "95s", "94s", "93s", "92s", "87s", "86s", "85s",
            "84s", "83s", "82s", "76s", "75s", "74s", "73s",
            "72s", "65s", "64s", "63s", "62s", "54s", "53s",
            "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo",
            "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o",
            "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o",
            "K7o", "K6o", "K5o", "K4o", "K3o", "K2o", "QJo",
            "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o",
            "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o",
            "T9o", "T8o", "T7o", "98o", "87o", "76o",
        }),
        "push_5bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
            "55", "44", "33", "22", "AKs", "AQs", "AJs", "ATs",
            "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "JTs",
            "T9s",
        }),
        "push_lt5bb": frozenset({
            "A2s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
            "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
            "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
            "98s", "97s", "96s", "95s", "94s", "93s", "92s",
            "87s", "86s", "85s", "84s", "83s", "82s",
            "76s", "75s", "74s", "73s", "72s",
            "65s", "64s", "63s", "62s",
            "54s", "53s", "52s",
            "43s", "42s",
            "32s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o",
            "A5o", "A4o", "A3o", "A2o",
            "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o",
            "K4o", "K3o", "K2o",
            "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o",
            "Q3o", "Q2o",
            "JTo", "J9o", "J8o", "J7o", "J6o",
            "T9o", "T8o", "T7o",
            "98o", "87o", "76o",
        }),
    },
    "UTG+1": {
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
            "55", "44", "33", "22", "AKs", "AQs", "AJs", "ATs",
            "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
            "K6s", "K5s", "K4s", "K3s", "K2s", "QJs", "QTs",
            "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s",
            "Q2s", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s",
            "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s",
            "T5s", "T4s", "T3s", "T2s", "98s", "97s", "96s",
            "95s", "94s", "93s", "92s", "87s", "86s", "85s",
            "84s", "83s", "82s", "76s", "75s", "74s", "73s",
            "72s", "65s", "64s", "63s", "62s", "54s", "53s",
            "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo",
            "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o",
            "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o",
            "K7o", "K6o", "K5o", "K4o", "K3o", "K2o", "QJo",
            "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o",
            "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o",
            "T9o", "T8o", "T7o", "98o", "87o", "76o",
        }),
        "push_5bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s",
            "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "JTs", "T9s",
        }),
        "push_lt5bb": frozenset({
            "22", "A3s", "A2s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
            "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
            "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
            "98s", "97s", "96s", "95s", "94s", "93s", "92s",
            "87s", "86s", "85s", "84s", "83s", "82s",
            "76s", "75s", "74s", "73s", "72s",
            "65s", "64s", "63s", "62s",
            "54s", "53s", "52s",
            "43s", "42s",
            "32s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o",
            "A5o", "A4o", "A3o", "A2o",
            "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o",
            "K4o", "K3o", "K2o",
            "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o",
            "Q3o", "Q2o",
            "JTo", "J9o", "J8o", "J7o", "J6o",
            "T9o", "T8o", "T7o",
            "98o", "87o", "76o",
        }),
    },
    "UTG+2": {
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
            "55", "44", "33", "22", "AKs", "AQs", "AJs", "ATs",
            "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s",
            "K6s", "K5s", "K4s", "K3s", "K2s", "QJs", "QTs",
            "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s",
            "Q2s", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s",
            "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s",
            "T5s", "T4s", "T3s", "T2s", "98s", "97s", "96s",
            "95s", "94s", "93s", "87s", "86s", "85s", "84s",
            "83s", "76s", "75s", "74s", "65s", "64s", "63s",
            "54s", "53s", "43s", "AKo", "AQo", "AJo", "ATo",
            "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o",
            "A2o", "KQo", "KJo", "KTo", "K9o", "K8o", "K7o",
            "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo",
            "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o", "Q3o",
            "JTo", "J9o", "J8o", "J7o", "J6o", "T9o", "T8o",
            "T7o", "98o", "87o", "76o",
        }),
        "push_5bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "KQo", "KJo",
        }),
        "push_lt5bb": frozenset({
            "22", "A2s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
            "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
            "98s", "97s", "96s", "95s", "94s", "93s",
            "87s", "86s", "85s", "84s", "83s",
            "76s", "75s", "74s",
            "65s", "64s", "63s",
            "54s", "53s",
            "43s",
            "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
            "KTo", "K9o", "K8o", "K7o", "K6o", "K5o", "K4o", "K3o", "K2o",
            "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o", "Q3o",
            "JTo", "J9o", "J8o", "J7o", "J6o",
            "T9o", "T8o", "T7o",
            "98o", "87o", "76o",
        }),
    },
    "LJ": {
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55",
            "44", "33", "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s",
            "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KJs", "KTs", "K9s", "K8s",
            "K7s", "K6s", "K5s", "K4s", "K3s", "K2s", "QJs", "QTs", "Q9s", "Q8s",
            "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s", "J8s", "J7s",
            "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "87s",
            "86s", "85s", "84s", "76s", "75s", "74s", "65s", "64s", "63s", "54s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o",
            "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o",
            "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o",
            "Q4o", "Q3o", "JTo", "J9o", "J8o", "J7o", "J6o", "J5o", "J4o", "T9o",
            "T8o", "T7o", "T6o", "98o", "97o", "96o", "87o", "86o", "76o",
        }),
    },
    "HJ": {
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s",
            "A3s", "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s",
            "K3s", "K2s", "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s",
            "Q2s", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s",
            "T8s", "T7s", "T6s", "T4s", "T3s", "T2s", "98s", "97s", "96s", "94s", "93s",
            "87s", "86s", "85s", "84s", "76s", "75s", "74s", "65s", "64s", "63s", "54s",
            "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A3o", "A2o",
            "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o", "K3o", "K2o", "QJo",
            "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o", "Q4o", "Q3o", "Q2o", "JTo", "J9o",
            "J8o", "J7o", "J6o", "J5o", "T9o", "T8o", "T7o", "T6o", "98o", "97o", "96o",
            "87o", "86o", "76o",
        }),
    },
    "CO": {
        "push": frozenset({
            "AA", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "AKo",
            "KK", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s", "AQo", "KQo",
            "QQ", "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "AJo", "KJo", "QJo",
            "JJ", "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "ATo", "KTo", "QTo", "JTo",
            "TT", "T9s", "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s", "A9o", "K9o", "Q9o", "J9o", "T9o",
            "99", "98s", "97s", "96s", "95s", "94s", "93s", "A8o", "K8o", "Q8o", "J8o", "T8o", "98o",
            "88", "87s", "86s", "85s", "84s", "A7o", "K7o", "Q7o", "J7o", "T7o", "97o", "87o",
            "77", "76s", "75s", "74s", "A6o", "K6o", "Q6o", "J6o", "T6o", "96o", "86o", "76o",
            "66", "65s", "64s", "A5o", "K5o", "Q5o", "J5o",
            "55", "54s", "A4o", "K4o", "Q4o",
            "44", "A3o", "K3o", "Q3o",
            "33", "A2o", "K2o", "Q2o",
            "22",
        }),
    },
    "BTN": {
        "push": frozenset({
            "22", "33", "44", "53s", "54s", "55", "63s", "64s", "65o", "66",
            "74s", "75s", "76o", "76s", "77", "84s", "85o", "86o", "86s", "87o",
            "87s", "88", "92s", "93s", "94s", "95o", "96o", "96s", "97o", "97s",
            "98o", "98s", "99", "A2o", "A2s", "A3o", "A3s", "A4o", "A4s", "A5o",
            "A5s", "A6o", "A6s", "A7o", "A7s", "A8o", "A8s", "A9o", "A9s", "AA",
            "AJo", "AJs", "AKo", "AKs", "AQo", "AQs", "ATo", "ATs", "J4s", "J5o",
            "J5s", "J6o", "J6s", "J7o", "J7s", "J8o", "J8s", "J9o", "J9s", "JJ",
            "JTo", "JTs", "K2o", "K2s", "K3o", "K3s", "K4o", "K4s", "K5o", "K5s",
            "K6o", "K6s", "K7o", "K7s", "K8o", "K8s", "K9o", "K9s", "KJo", "KJs",
            "KK", "KQo", "KQs", "KTo", "KTs", "Q2o", "Q2s", "Q3o", "Q3s", "Q4o",
            "Q4s", "Q5o", "Q5s", "Q6o", "Q6s", "Q7o", "Q7s", "Q8o", "Q8s", "Q9o",
            "Q9s", "QJo", "QJs", "QQ", "QTo", "QTs", "T4o", "T4s", "T6o", "T6s",
            "T7o", "T7s", "T8o", "T8s", "T9o", "T9s", "TT",
        }),
    },
    "SB": {
        "push_5bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o",
            "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o",
            "K7o", "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o",
            "Q5o", "Q4o", "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o", "J5o", "J4o", "J3o",
            "J2o", "T9o", "T8o", "T7o", "T6o", "T5o", "T4o", "98o", "97o", "96o", "87o", "86o",
            "85o", "76o", "65o",
        }),
        "push_lt5bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o",
            "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o",
            "K7o", "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o",
            "Q5o", "Q4o", "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o", "J5o", "J4o", "J3o",
            "J2o", "T9o", "T8o", "T7o", "T6o", "T5o", "T4o", "98o", "97o", "96o", "95o", "87o",
            "86o", "85o", "76o", "65o",
        }),
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o",
            "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o",
            "K7o", "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o",
            "Q5o", "Q4o", "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o", "J5o", "J4o", "J3o",
            "J2o", "T9o", "T8o", "T7o", "T6o", "T5o", "T4o", "98o", "97o", "96o", "95o", "87o",
            "86o", "85o", "76o", "65o",
        }),
    },
}


ICM_PUSH_FOLD_6_10BB: Dict[str, Dict[str, HandSet]] = {
    "UTG+1": {
        "push_10bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AQs", "AJs", "ATs",
            "A9s", "A5s", "A4s", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "AKo", "AQo",
        }),
        "push_6_9bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "AKs",
            "AQs", "AJs", "ATs", "A9s", "A8s", "A5s", "A4s", "KQs", "KJs", "KTs", "K9s",
            "QJs", "QTs", "Q9s", "JTs", "T9s", "AKo", "AQo", "AJo", "ATo", "KQo",
        }),
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "AKs",
            "AQs", "AJs", "ATs", "A9s", "A8s", "A5s", "A4s", "KQs", "KJs", "KTs", "K9s",
            "QJs", "QTs", "Q9s", "JTs", "T9s", "AKo", "AQo", "AJo", "ATo", "KQo",
        }),
    },
    "UTG+2": {
        "push_10bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "AKs", "AQs",
            "AJs", "ATs", "A9s", "A5s", "KQs", "KJs", "KTs", "QJs", "QTs", "JTs", "AKo",
            "AQo", "AJo",
        }),
        "push_6_9bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "AKs",
            "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "KQs", "KJs",
            "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s", "AKo", "AQo", "AJo",
            "ATo", "KQo",
        }),
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "AKs",
            "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "KQs", "KJs",
            "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s", "AKo", "AQo", "AJo",
            "ATo", "KQo",
        }),
    },
    "LJ": {
        "push_10bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A5s", "KQs", "KJs", "KTs",
            "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s", "AKo", "AQo", "AJo", "ATo",
            "KQo", "KJo",
        }),
        "push_6_9bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s",
            "T8s", "98s", "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "KQo", "KJo",
            "QJo",
        }),
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
            "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "QJs", "QTs", "Q9s", "JTs", "J9s", "T9s",
            "T8s", "98s", "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "KQo", "KJo",
            "QJo",
        }),
    },
    "SB": {
        "push_10bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
            "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o", "K7o",
            "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "JTo", "J9o", "J8o",
            "T9o", "T8o", "T7o", "98o", "97o", "87o", "76o", "65o", "54o",
        }),
        "push_6_9bb": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
            "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o", "K7o",
            "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o",
            "Q4o", "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o", "T9o", "T8o", "T7o", "98o",
            "97o", "87o", "76o", "65o", "54o",
        }),
        "push": frozenset({
            "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33",
            "22", "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
            "A2s", "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
            "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s", "JTs", "J9s",
            "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s", "T9s", "T8s", "T7s", "T6s", "T5s",
            "T4s", "T3s", "T2s", "98s", "97s", "96s", "95s", "94s", "93s", "92s", "87s", "86s",
            "85s", "84s", "83s", "82s", "76s", "75s", "74s", "73s", "72s", "65s", "64s", "63s",
            "62s", "54s", "53s", "52s", "43s", "42s", "32s", "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
            "A7o", "A6o", "A5o", "A4o", "A3o", "A2o", "KQo", "KJo", "KTo", "K9o", "K8o", "K7o",
            "K6o", "K5o", "K4o", "K3o", "K2o", "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o", "Q5o",
            "Q4o", "Q3o", "Q2o", "JTo", "J9o", "J8o", "J7o", "J6o", "T9o", "T8o", "T7o", "98o",
            "97o", "87o", "76o", "65o", "54o",
        }),
    },
}


# Placeholder for 10-15bb and 16-20bb ranges (to be completed)
ICM_PUSH_FOLD_10_15BB: Dict[str, Dict[str, HandSet]] = {
    # TODO: Add 10-15bb push/fold ranges
}

ICM_PUSH_FOLD_16_20BB: Dict[str, Dict[str, HandSet]] = {
    # TODO: Add 16-20bb push/fold ranges
}


# Combined ICM push/fold lookup
ICM_PUSH_FOLD: Dict[str, Dict[str, Dict[str, HandSet]]] = {
    "1-5bb": ICM_PUSH_FOLD_1_5BB,
    "6-10bb": ICM_PUSH_FOLD_6_10BB,
    "10-15bb": ICM_PUSH_FOLD_10_15BB,
    "16-20bb": ICM_PUSH_FOLD_16_20BB,
}


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------

def get_stack_bucket(stack_bb: float) -> str:
    """
    Get stack bucket for ICM push/fold lookup.
    
    Args:
        stack_bb: Stack size in big blinds
    
    Returns:
        Stack bucket string: "1-5bb", "6-10bb", "10-15bb", "16-20bb", or "deep"
    """
    if stack_bb < 1:
        return "1-5bb"
    elif stack_bb <= 5:
        return "1-5bb"
    elif stack_bb <= 10:
        return "6-10bb"
    elif stack_bb <= 15:
        return "10-15bb"
    elif stack_bb <= 20:
        return "16-20bb"
    else:
        return "deep"


def is_short_stack(stack_bb: float) -> bool:
    """Check if stack is in push/fold territory (<= 10bb)."""
    return stack_bb <= 10


def is_icm_push_fold_zone(stack_bb: float) -> bool:
    """Check if stack is in ICM push/fold zone (<= 20bb)."""
    return stack_bb <= 20
