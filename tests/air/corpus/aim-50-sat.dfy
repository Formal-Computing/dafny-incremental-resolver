// Generated from original SATLIB DIMACS; this program does NOT solve SAT.
// aim-50-1_6-yes1-1.cnf; SHA-256 d96f1edb1db3d0e55a3ff0f7707517e41a79374acbb857df051e5441ab27657d; reported SATLIB class: SAT
module CorpusProvider {
  const VariableCount: nat := 50
  const C000: seq<int> := [5, 28, 41]
  const C001: seq<int> := [5, -28, 41]
  const C002: seq<int> := [10, 30, -41]
  const C003: seq<int> := [5, -10, -41]
  const C004: seq<int> := [-5, 25, 30]
  const C005: seq<int> := [-5, -25, 30]
  const C006: seq<int> := [11, -30, -33]
  const C007: seq<int> := [-11, -30, -33]
  const C008: seq<int> := [7, -30, 33]
  const C009: seq<int> := [-7, 14, 33]
  const C010: seq<int> := [-4, -7, -14]
  const C011: seq<int> := [4, -14, -29]
  const C012: seq<int> := [-1, -14, 32]
  const C013: seq<int> := [-1, 4, -32]
  const C014: seq<int> := [1, 24, 29]
  const C015: seq<int> := [1, -24, -34]
  const C016: seq<int> := [-6, -24, 34]
  const C017: seq<int> := [6, -24, 38]
  const C018: seq<int> := [6, -32, -38]
  const C019: seq<int> := [32, 44, 48]
  const C020: seq<int> := [-38, -44, 48]
  const C021: seq<int> := [22, 29, -48]
  const C022: seq<int> := [22, -29, 32]
  const C023: seq<int> := [-22, -25, -48]
  const C024: seq<int> := [-22, 25, 40]
  const C025: seq<int> := [18, -22, -40]
  const C026: seq<int> := [-18, 20, -40]
  const C027: seq<int> := [-18, 28, -40]
  const C028: seq<int> := [-18, -28, 39]
  const C029: seq<int> := [-28, 35, -39]
  const C030: seq<int> := [-35, -39, 43]
  const C031: seq<int> := [-35, -43, -50]
  const C032: seq<int> := [-43, -45, 50]
  const C033: seq<int> := [31, 45, 50]
  const C034: seq<int> := [-31, -44, 45]
  const C035: seq<int> := [-15, 44, 49]
  const C036: seq<int> := [-15, -31, -49]
  const C037: seq<int> := [15, -31, 36]
  const C038: seq<int> := [15, 23, -36]
  const C039: seq<int> := [-23, -36, 46]
  const C040: seq<int> := [20, 27, -46]
  const C041: seq<int> := [-20, -23, 27]
  const C042: seq<int> := [-16, -27, -46]
  const C043: seq<int> := [16, 26, -27]
  const C044: seq<int> := [16, 17, -26]
  const C045: seq<int> := [2, 13, -17]
  const C046: seq<int> := [2, -13, -26]
  const C047: seq<int> := [-5, -17, -26]
  const C048: seq<int> := [-2, -17, 42]
  const C049: seq<int> := [-2, 12, -13]
  const C050: seq<int> := [-2, -12, -42]
  const C051: seq<int> := [8, 13, -42]
  const C052: seq<int> := [-8, -10, 13]
  const C053: seq<int> := [3, -8, 10]
  const C054: seq<int> := [-3, 10, -37]
  const C055: seq<int> := [-3, 10, -47]
  const C056: seq<int> := [10, 19, 47]
  const C057: seq<int> := [-12, -19, 47]
  const C058: seq<int> := [12, -19, 21]
  const C059: seq<int> := [9, -19, -21]
  const C060: seq<int> := [-9, -11, -21]
  const C061: seq<int> := [-9, 11, -49]
  const C062: seq<int> := [11, 41, 49]
  const C063: seq<int> := [19, -32, 37]
  const C064: seq<int> := [-1, 39, -50]
  const C065: seq<int> := [8, 17, 40]
  const C066: seq<int> := [38, 43, 49]
  const C067: seq<int> := [23, 42, -47]
  const C068: seq<int> := [-13, -29, 37]
  const C069: seq<int> := [-34, 37, -47]
  const C070: seq<int> := [-33, -37, 50]
  const C071: seq<int> := [-6, 14, 34]
  const C072: seq<int> := [9, -20, -50]
  const C073: seq<int> := [35, 36, 38]
  const C074: seq<int> := [3, 31, 46]
  const C075: seq<int> := [7, -16, 21]
  const C076: seq<int> := [-6, 17, 26]
  const C077: seq<int> := [23, 24, 46]
  const C078: seq<int> := [18, 24, -45]
  const C079: seq<int> := [-4, -6, 7]
  const Clauses: seq<seq<int>> := [
    C000, C001, C002, C003, C004, C005, C006, C007, C008, C009, C010, C011,
    C012, C013, C014, C015, C016, C017, C018, C019, C020, C021, C022, C023,
    C024, C025, C026, C027, C028, C029, C030, C031, C032, C033, C034, C035,
    C036, C037, C038, C039, C040, C041, C042, C043, C044, C045, C046, C047,
    C048, C049, C050, C051, C052, C053, C054, C055, C056, C057, C058, C059,
    C060, C061, C062, C063, C064, C065, C066, C067, C068, C069, C070, C071,
    C072, C073, C074, C075, C076, C077, C078, C079
  ]
  function SourceVersion(): int { 0 }
}
module CorpusInspector {
  import Src = CorpusProvider
  function ClauseCount(): nat { |Src.Clauses| }
}
module CorpusWorkingEdit {
  function RevisionTag(): int { 10 }
}
