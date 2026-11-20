# RADXOID v1.0.5 — Installer asset handling fix

Correção do installer Windows/Linux para o layout real dos assets GitHub da imagem v1.0.4.

## Correções

- Aceita `SHA256SUMS-v1.0.5.txt` além de `SHA256SUMS.txt`.
- Trata `rkupdate.img` como imagem completa; não concatena o `.zip` com o `.img`.
- Verifica o `.img` e o `.zip` separadamente.
- Copia a imagem completa para `update.img`, nome esperado pelo fluxo Linux.
- Mantém compatibilidade com volumes legados `.001`, `.002`, etc.
- Mantém o bloqueio contra caminhos, symlinks e manifestos incompletos.

A imagem Android publicada permanece a mesma imagem v1.0.4 já verificada:

- `rk356x_rock_3a_r_20261120.1320_rkupdate.img`
- `rk356x_rock_3a_r_20261120.1320_rkupdate.zip`
- `rk356x_rock_3a_r_20261120.1320_gpt.zip`
- `super.img`

O `.img` e o `.zip` são representações diferentes do mesmo asset, não partes para unir.
