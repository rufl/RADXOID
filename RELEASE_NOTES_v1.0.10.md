# RADXOID v1.0.10 — installer worker startup fix

- Corrige a inicialização das threads de checksum e join.
- Corrige o caso em que a GUI ficava em `0%` sem gerar logs.
- Usa flags explícitas para impedir duplicação de workers durante re-renderizações.
- Mantém progresso e logs processados pela thread principal do Tkinter.

Os assets da imagem permanecem os mesmos da v1.0.9.
