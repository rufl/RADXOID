# RADXOID v1.0.6 — Installer progress feedback

- Desativa `Next` enquanto SHA-256 ou união está em andamento.
- Mostra que imagens grandes podem levar vários minutos.
- Atualiza logs e status da GUI somente na thread principal do Tkinter.
- Agenda a atualização da tela após checksum/join, evitando chamadas Tkinter de threads de trabalho.
- Mantém a correção v1.0.5 para `rkupdate.img` completo, `.zip` separado e manifesto versionado.

Os assets da imagem permanecem os mesmos da v1.0.4/v1.0.5.
