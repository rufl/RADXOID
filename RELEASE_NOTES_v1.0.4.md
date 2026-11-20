# RADXOID v1.0.4 — Android 11 ROCK 3A

Build lean `userdebug` para Radxa ROCK 3A / RK3568, com o bloco QOL incluído no sistema.

## QOL incluído

- Setup Wizard desativado para uso dedicado em HDMI.
- `LatinIME` e `PackageInstaller` pré-otimizados.
- Velocidade de ponteiro confortável por padrão.
- Bolhas de notificação e pulso de LED desativados.
- Perfil ADB reversível disponível em `scripts/apply-device-qol.sh`.
- Sem ADB irrestrito adicional e sem redução de SELinux.

## Artefatos

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `rk356x_rock_3a_r_20261120.1320_rkupdate.img` | 1,824,689,396 B | `a2bfc062fbb753810140cd85bfdd16e6bbe65c7c376a1fd6b4c969cfcd860ade` |
| `rk356x_rock_3a_r_20261120.1320_rkupdate.zip` | 805,040,757 B | `7875b5e7e704aa07642c2c475852bb433f982015155aaf7fbead0063dad4c3c3` |
| `rk356x_rock_3a_r_20261120.1320_gpt.zip` | 804,638,431 B | `031a1974e52f64b7153f0b64225dec0d508735faddcffe7c0825dff15268f991` |
| `super.img` | 1,665,322,592 B | `6e458dbd08b8469e2f5d2e8c19861c44444074b708b2bc703dbf3665feb33f3f` |

Os arquivos `gpt.zip` e `rkupdate.zip` são os pacotes distribuíveis; o `.img` de GPT bruto tem 4,391,454,208 bytes e não é publicado diretamente por exceder o limite de asset do GitHub.

## Build e verificação

- Fonte: Android 11 / `Android11_Radxa_rk12`.
- Produto: `rk356x_rock_3a_r-userdebug`.
- Flavor: lean (`ROCK3A_ENV=lean`).
- Build reproduzível em container Ubuntu 20.04 `radxoid-builder:u20.04`.
- Build Android, kernel, U-Boot, empacotamento Rockchip e hashes SHA-256 concluídos com sucesso.
- Avisos não fatais do BSP: conversões de tipos nos drivers Wi-Fi, exports duplicados no `modpost`, `io-domain.sh` com testes `[` incompatíveis e sandbox Soong desativado por erro do nsjail.

## Limites

A imagem não foi inicializada em uma placa ROCK 3A nesta execução. Não houve gravação em cartão SD nem teste de boot, GPU, Wi-Fi, térmica ou controles. Verifique o dispositivo de destino antes de gravar: o processo de flash destrói os dados existentes.
