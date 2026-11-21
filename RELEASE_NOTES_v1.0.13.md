# RADXOID v1.0.13 — fully graphical SD-card writing

- Adiciona gravação direta de `update.img` em SD card pela GUI.
- Windows: exige Administrator, lista candidatos SD/USB removíveis e desmonta volumes.
- Linux: usa root ou autorização gráfica `pkexec`.
- Revalida dispositivo e capacidade imediatamente antes da escrita.
- Mostra fase, bytes, percentual e logs para validação, desmontagem, escrita, flush, hash da origem e readback.
- Faz verificação SHA-256 do conteúdo escrito antes de concluir.
- Exige confirmação exata `ERASE <device>` e bloqueia controles durante a operação.

Os assets da imagem permanecem os mesmos das releases anteriores.
