# Toolkit Soulash 2 — fluxo local

Fontes: Soulash 2 0.10.5, JSON UTF-8 e listas TXT em data/mods/core_2.
Destino planejado: PTBR/data/mods/ptbr, instalado na raiz do jogo.

As traduções reutilizadas da versão 0.10.1 exigem revisão linguística. Nenhuma entrada foi automaticamente aprovada. Os arquivos antigos english/, ptbr/ e os pacotes existentes foram preservados.

## Uso

Python 3.11 ou superior, apenas biblioteca padrão:

```sh
python translation-work/toolkit.py status
python translation-work/toolkit.py check
python translation-work/toolkit.py update-sources --game-root "/path/to/Soulash 2" --dry-run
python translation-work/toolkit.py doctor
```

O preflight de destino é `python3 translation-work/toolkit.py doctor --arm64`. Execução em Ubuntu ARM64 não verificada. O comando verifica fontes e integridade e reconstrói uma fixture em diretório temporário, sem alterar traduções.

`apply` recebe JSON com generation, expected_count e entries. Cada entrada inclui id, source_fingerprint e PTBR; reviewed e gender são decisões explícitas da revisão. Build exige todas as entradas revisadas. Use export-payload para gerar o envelope de aplicação. Consulte docs/release.md para a publicação e seus limites de verificação.

## Verificação e limites

O briefing e o fluxo estão em docs/. Execute `python -m unittest discover -s translation-work/tests -v`. Compilação e fixtures são verificadas no Windows; execução Ubuntu ARM64 e testes dentro do jogo permanecem não verificados. Publicação real não foi executada. O cliente de Release foi exercitado com publicação HTTP simulada, primeira versão, incremento, repetição, rascunho interrompido, commit antigo e anexos inesperados. Não há build de distribuição enquanto a revisão não estiver completa.

Retenção local implementada: 10 transações, 512 MiB. `gc --dry-run` lista limpeza elegível; `recover` restaura operações interrompidas; `rollback` restaura a última transação compatível. O histórico Git continua necessário para recuperação durável.

## Política do README público

Contagens e progresso permanecem nesta documentação e nos manifestos. O README público usa links estáveis e instruções condicionais; Releases não devem reescrevê-lo.

## Licenciamento

A mudança para CC BY-NC-SA 4.0 foi autorizada pelo mantenedor em 30/10/2026. A licença anterior está preservada em reference/AGPL-3.0-legacy.txt. Direitos de recursos originais do jogo permanecem com seus titulares. A permissão comercial adicional cobre somente direitos efetivamente autorizados.

## Corpus migrado

Soulash 2 0.10.5: 5.987 fontes, 29.434 unidades em 59 lotes. Foram reaproveitadas 25.249 traduções compatíveis da versão 0.10.1; 4.185 permanecem vazias. Todas as unidades exigem revisão explícita. A tradução privada e seu histórico estão preservados conforme docs/migracao.md.

## Primeiros passos

Clone/pull → `python3 translation-work/toolkit.py doctor --arm64` → leia docs/briefing-do-jogo.md e docs/fluxo-de-traducao.md → status/resume → revise/traduza os lotes. Não execute build até concluir a revisão. A instalação do jogo é exclusivamente fonte de leitura.

## Comandos disponíveis

extract, sync, update-sources, export-payload, apply, check, status, resume, diff, build, verify-output, package, doctor, gc, recover e rollback. Todos resolvem o repositório pelo caminho do script. As saídas são JSON; falhas retornam código não zero. `--dry-run` é aceito apenas em extract, sync, update-sources e gc.
