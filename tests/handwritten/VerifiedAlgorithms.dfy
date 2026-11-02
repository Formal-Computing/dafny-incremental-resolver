// Purpose-built proof-bearing Dafny project (not a converted CNF).
// Dependency graph: Arithmetic, Search, Provider -> Client; Independent is unrelated.
module Arithmetic {
  method CountUp(n: nat) returns (count: nat)
    ensures count == n
  {
    var i: nat := 0;
    count := 0;
    while i < n
      invariant i <= n
      invariant count == i
      decreases n - i
    {
      i := i + 1;
      count := count + 1;
    }
  }

  function SumPrefix(a: array<int>, n: nat): int
    requires n <= a.Length
    reads a
    decreases n
  {
    if n == 0 then 0 else SumPrefix(a, n - 1) + a[n - 1]
  }

  method SumArray(a: array<int>) returns (sum: int)
    ensures sum == SumPrefix(a, a.Length)
  {
    var i: nat := 0;
    sum := 0;
    while i < a.Length
      invariant i <= a.Length
      invariant sum == SumPrefix(a, i)
      decreases a.Length - i
    {
      sum := sum + a[i];
      i := i + 1;
    }
  }
}

module Search {
  method FindFirst(a: array<int>, target: int) returns (index: int)
    ensures -1 <= index < a.Length
    ensures index >= 0 ==> a[index] == target
    ensures index == -1 ==> forall k :: 0 <= k < a.Length ==> a[k] != target
  {
    var i: nat := 0;
    while i < a.Length
      invariant i <= a.Length
      invariant forall k :: 0 <= k < i ==> a[k] != target
      decreases a.Length - i
    {
      if a[i] == target {
        return i;
      }
      i := i + 1;
    }
    return -1;
  }
}

module Provider {
  function Offset(x: int): int { x + 1 }

  method Increment(x: int) returns (result: int)
    ensures result == Offset(x)
  {
    result := x + 1;
  }
}

module Client {
  import P = Provider
  import A = Arithmetic
  import S = Search

  method CheckProvider(x: int) {
    assert P.Offset(x) == x + 1;
  }

  method CheckCounter(n: nat) {
    var count := A.CountUp(n);
    assert count == n;
  }

  method CheckSearch(a: array<int>, needle: int) {
    var index := S.FindFirst(a, needle);
    assert index < 0 || a[index] == needle;
  }
}

module Independent {
  function RevisionTag(): int { 10 }

  method Abs(x: int) returns (y: nat)
    ensures y >= 0
    ensures x >= 0 ==> y == x
    ensures x < 0 ==> y == -x
  {
    if x >= 0 { y := x; }
    else { y := -x; }
  }

  method Triangle(a: int, b: int, c: int)
    requires 0 <= a && 0 <= b && 0 <= c
    requires a + b >= c && b + c >= a && a + c >= b
  {
    assert a + b >= c;
    assert b + c >= a;
  }
}
