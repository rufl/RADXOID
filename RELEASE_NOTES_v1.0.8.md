# RADXOID v1.0.8 — percentage progress and SHA skip

- Mostra progresso percentual real durante SHA-256, baseado nos bytes lidos.
- Mostra progresso percentual real durante a cópia/união dos assets.
- Exibe o percentual no status bar e na barra de progresso.
- Permite pular SHA-256 somente após confirmação explícita de risco.
- Interrompe a leitura SHA no próximo bloco de 4 MiB após o skip.
- Mantém `Next` bloqueado durante operações normais e marca o skip como inseguro.

Os assets da imagem permanecem os mesmos das releases anteriores.
