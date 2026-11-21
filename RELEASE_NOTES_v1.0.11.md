# RADXOID v1.0.11 — visible logs and complete-asset join diagnostics

- Mantém o painel de logs fora da área dinâmica das etapas.
- Os logs agora permanecem visíveis ao avançar entre etapas.
- Registra explicitamente quando não existem volumes `.001`, `.002`, etc.
- Valida o tamanho de cada arquivo copiado antes de concluir.
- Registra o diretório final de saída.
- Assets completos continuam sendo normalizados: `rkupdate.img` vira `update.img`; `.zip` e `super.img` são copiados separadamente.

Os assets da imagem permanecem os mesmos das releases anteriores.
