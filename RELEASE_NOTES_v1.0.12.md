# RADXOID v1.0.12 — no volume join stage

- Remove a etapa enganosa `Join Volumes` da GUI e da CLI.
- O fluxo agora verifica, prepara e copia assets completos.
- `rkupdate.img` é normalizado para `update.img`; `super.img` e `.zip` permanecem separados.
- Entradas `.001`, `.002`, etc. são rejeitadas porque não fazem parte do pacote distribuído.
- Progresso e logs continuam visíveis durante a preparação.

Os assets da imagem permanecem os mesmos das releases anteriores.
