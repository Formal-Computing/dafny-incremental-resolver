// To observe a cache hit, make a same-length change inside module A,
// then resolve the document again through Dafny's language server.
module A {
  function F(x: int): int { x + 1 }
}

module B {
  function G(x: int): int { x * 2 }
}
