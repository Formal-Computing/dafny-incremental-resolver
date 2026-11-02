// Generated from original SATLIB DIMACS; this program does NOT solve SAT.
// aim-50-1_6-no-1.cnf; SHA-256 17d42ca0ef48f3a0523a4a9f0a9f683da9acdc9a61f175dc9e143398e6532a86; reported SATLIB class: UNSAT
module CorpusProvider {
  const VariableCount: nat := 50
  const C000: seq<int> := [16, 23, 42]
  const C001: seq<int> := [-16, 23, 42]
  const C002: seq<int> := [26, 41, -42]
  const C003: seq<int> := [-26, 41, -42]
  const C004: seq<int> := [32, -41, -42]
  const C005: seq<int> := [6, 15, -41]
  const C006: seq<int> := [-6, 15, -32]
  const C007: seq<int> := [1, -32, 46]
  const C008: seq<int> := [-1, -32, 46]
  const C009: seq<int> := [-15, -41, -46]
  const C010: seq<int> := [-15, -21, -46]
  const C011: seq<int> := [-23, 33, 38]
  const C012: seq<int> := [-23, -33, 38]
  const C013: seq<int> := [8, 22, 33]
  const C014: seq<int> := [8, 22, -33]
  const C015: seq<int> := [-22, 37, -38]
  const C016: seq<int> := [13, 36, -37]
  const C017: seq<int> := [13, -22, -36]
  const C018: seq<int> := [-13, -22, -37]
  const C019: seq<int> := [11, -23, 47]
  const C020: seq<int> := [-8, 11, -47]
  const C021: seq<int> := [-8, -11, 39]
  const C022: seq<int> := [-11, 27, -39]
  const C023: seq<int> := [-8, -11, -39]
  const C024: seq<int> := [-7, 26, 29]
  const C025: seq<int> := [-7, -26, 29]
  const C026: seq<int> := [-13, 20, 36]
  const C027: seq<int> := [-13, 17, 20]
  const C028: seq<int> := [5, -17, 20]
  const C029: seq<int> := [5, -19, -45]
  const C030: seq<int> := [-5, -10, -45]
  const C031: seq<int> := [6, 25, 47]
  const C032: seq<int> := [-6, -10, 25]
  const C033: seq<int> := [-2, -27, 37]
  const C034: seq<int> := [-27, -36, 40]
  const C035: seq<int> := [18, 39, -40]
  const C036: seq<int> := [-2, -19, 31]
  const C037: seq<int> := [5, 18, -30]
  const C038: seq<int> := [-31, -43, -50]
  const C039: seq<int> := [10, -30, 43]
  const C040: seq<int> := [10, -41, 43]
  const C041: seq<int> := [19, 21, 29]
  const C042: seq<int> := [37, 42, 45]
  const C043: seq<int> := [-20, 27, 40]
  const C044: seq<int> := [-21, -36, 48]
  const C045: seq<int> := [31, -36, -48]
  const C046: seq<int> := [3, -9, -18]
  const C047: seq<int> := [16, -40, -47]
  const C048: seq<int> := [1, -18, 21]
  const C049: seq<int> := [2, 28, 32]
  const C050: seq<int> := [-1, -24, -50]
  const C051: seq<int> := [-12, 35, 49]
  const C052: seq<int> := [-6, -36, 45]
  const C053: seq<int> := [7, 12, -43]
  const C054: seq<int> := [7, 30, -43]
  const C055: seq<int> := [-5, 9, -17]
  const C056: seq<int> := [3, 14, 50]
  const C057: seq<int> := [-12, 17, -49]
  const C058: seq<int> := [24, 34, 49]
  const C059: seq<int> := [14, -20, 24]
  const C060: seq<int> := [-9, 35, -49]
  const C061: seq<int> := [-4, -47, 50]
  const C062: seq<int> := [4, 44, -44]
  const C063: seq<int> := [28, -28, -38]
  const C064: seq<int> := [2, 4, -48]
  const C065: seq<int> := [-20, 35, -44]
  const C066: seq<int> := [30, -31, -43]
  const C067: seq<int> := [-14, -29, 35]
  const C068: seq<int> := [-20, 35, -35]
  const C069: seq<int> := [19, -22, -24]
  const C070: seq<int> := [-25, -28, 48]
  const C071: seq<int> := [-14, -34, 44]
  const C072: seq<int> := [9, 20, 44]
  const C073: seq<int> := [-3, 9, -29]
  const C074: seq<int> := [17, 34, -34]
  const C075: seq<int> := [12, 48]
  const C076: seq<int> := [-12, -25, -43]
  const C077: seq<int> := [-25, -31, 48]
  const C078: seq<int> := [14, -16, 49]
  const C079: seq<int> := [-3, -4, -35]
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
