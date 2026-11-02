// Generated from original SATLIB DIMACS; this program does NOT solve SAT.
// uf20-01.cnf; SHA-256 bbb43578ee4f0634de44a7632b6df4ee6b9204f1c82e77660616b0891b00eb24; reported SATLIB class: SAT
module CorpusProvider {
  const VariableCount: nat := 20
  const C000: seq<int> := [4, -18, 19]
  const C001: seq<int> := [3, 18, -5]
  const C002: seq<int> := [-5, -8, -15]
  const C003: seq<int> := [-20, 7, -16]
  const C004: seq<int> := [10, -13, -7]
  const C005: seq<int> := [-12, -9, 17]
  const C006: seq<int> := [17, 19, 5]
  const C007: seq<int> := [-16, 9, 15]
  const C008: seq<int> := [11, -5, -14]
  const C009: seq<int> := [18, -10, 13]
  const C010: seq<int> := [-3, 11, 12]
  const C011: seq<int> := [-6, -17, -8]
  const C012: seq<int> := [-18, 14, 1]
  const C013: seq<int> := [-19, -15, 10]
  const C014: seq<int> := [12, 18, -19]
  const C015: seq<int> := [-8, 4, 7]
  const C016: seq<int> := [-8, -9, 4]
  const C017: seq<int> := [7, 17, -15]
  const C018: seq<int> := [12, -7, -14]
  const C019: seq<int> := [-10, -11, 8]
  const C020: seq<int> := [2, -15, -11]
  const C021: seq<int> := [9, 6, 1]
  const C022: seq<int> := [-11, 20, -17]
  const C023: seq<int> := [9, -15, 13]
  const C024: seq<int> := [12, -7, -17]
  const C025: seq<int> := [-18, -2, 20]
  const C026: seq<int> := [20, 12, 4]
  const C027: seq<int> := [19, 11, 14]
  const C028: seq<int> := [-16, 18, -4]
  const C029: seq<int> := [-1, -17, -19]
  const C030: seq<int> := [-13, 15, 10]
  const C031: seq<int> := [-12, -14, -13]
  const C032: seq<int> := [12, -14, -7]
  const C033: seq<int> := [-7, 16, 10]
  const C034: seq<int> := [6, 10, 7]
  const C035: seq<int> := [20, 14, -16]
  const C036: seq<int> := [-19, 17, 11]
  const C037: seq<int> := [-7, 1, -20]
  const C038: seq<int> := [-5, 12, 15]
  const C039: seq<int> := [-4, -9, -13]
  const C040: seq<int> := [12, -11, -7]
  const C041: seq<int> := [-5, 19, -8]
  const C042: seq<int> := [1, 16, 17]
  const C043: seq<int> := [20, -14, -15]
  const C044: seq<int> := [13, -4, 10]
  const C045: seq<int> := [14, 7, 10]
  const C046: seq<int> := [-5, 9, 20]
  const C047: seq<int> := [10, 1, -19]
  const C048: seq<int> := [-16, -15, -1]
  const C049: seq<int> := [16, 3, -11]
  const C050: seq<int> := [-15, -10, 4]
  const C051: seq<int> := [4, -15, -3]
  const C052: seq<int> := [-10, -16, 11]
  const C053: seq<int> := [-8, 12, -5]
  const C054: seq<int> := [14, -6, 12]
  const C055: seq<int> := [1, 6, 11]
  const C056: seq<int> := [-13, -5, -1]
  const C057: seq<int> := [-7, -2, 12]
  const C058: seq<int> := [1, -20, 19]
  const C059: seq<int> := [-2, -13, -8]
  const C060: seq<int> := [15, 18, 4]
  const C061: seq<int> := [-11, 14, 9]
  const C062: seq<int> := [-6, -15, -2]
  const C063: seq<int> := [5, -12, -15]
  const C064: seq<int> := [-6, 17, 5]
  const C065: seq<int> := [-13, 5, -19]
  const C066: seq<int> := [20, -1, 14]
  const C067: seq<int> := [9, -17, 15]
  const C068: seq<int> := [-5, 19, -18]
  const C069: seq<int> := [-12, 8, -10]
  const C070: seq<int> := [-18, 14, -4]
  const C071: seq<int> := [15, -9, 13]
  const C072: seq<int> := [9, -5, -1]
  const C073: seq<int> := [10, -19, -14]
  const C074: seq<int> := [20, 9, 4]
  const C075: seq<int> := [-9, -2, 19]
  const C076: seq<int> := [-5, 13, -17]
  const C077: seq<int> := [2, -10, -18]
  const C078: seq<int> := [-18, 3, 11]
  const C079: seq<int> := [7, -9, 17]
  const C080: seq<int> := [-15, -6, -3]
  const C081: seq<int> := [-2, 3, -13]
  const C082: seq<int> := [12, 3, -2]
  const C083: seq<int> := [-2, -3, 17]
  const C084: seq<int> := [20, -15, -16]
  const C085: seq<int> := [-5, -17, -19]
  const C086: seq<int> := [-20, -18, 11]
  const C087: seq<int> := [-9, 1, -5]
  const C088: seq<int> := [-19, 9, 17]
  const C089: seq<int> := [12, -2, 17]
  const C090: seq<int> := [4, -16, -5]
  const Clauses: seq<seq<int>> := [
    C000, C001, C002, C003, C004, C005, C006, C007, C008, C009, C010, C011,
    C012, C013, C014, C015, C016, C017, C018, C019, C020, C021, C022, C023,
    C024, C025, C026, C027, C028, C029, C030, C031, C032, C033, C034, C035,
    C036, C037, C038, C039, C040, C041, C042, C043, C044, C045, C046, C047,
    C048, C049, C050, C051, C052, C053, C054, C055, C056, C057, C058, C059,
    C060, C061, C062, C063, C064, C065, C066, C067, C068, C069, C070, C071,
    C072, C073, C074, C075, C076, C077, C078, C079, C080, C081, C082, C083,
    C084, C085, C086, C087, C088, C089, C090
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
