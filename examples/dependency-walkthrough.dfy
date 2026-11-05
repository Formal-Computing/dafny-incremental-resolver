// Minimal hand-written verification example for the cache-invalidation discussion.
// The CLI verifier checks proof obligations; cache hits require the LSP tests.
module Provider {
  function Offset(x: int): int { x + 1 }
}

module Consumer {
  import opened Provider

  method Check(x: int) {
    assert Offset(x) == x + 1;
  }
}

module Independent {
  function Twice(x: int): int { x * 2 }

  method Check() {
    assert Twice(7) == 14;
  }
}
