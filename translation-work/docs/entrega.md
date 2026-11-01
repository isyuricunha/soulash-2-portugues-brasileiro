# Entrega e estados de validação

## Migração

O histórico Git privado está preservado em reference/private-history.bundle. O snapshot não secreto de 11.547 arquivos está em reference/private-worktree.zip, com inventário SHA-256 e testes de conferência. O diretório privado original permanece intacto. A tradução pública antiga também foi comparada às pendências; não houve reaproveitamento adicional inequívoco.

## Trabalho ativo

EN/data/mods/core_2 contém 5.987 fontes da versão 0.10.5. O workspace tem 29.434 unidades em 59 lotes: 25.249 PTBR recuperados e 4.185 vazios. Nenhum registro foi automaticamente aprovado. O destino de build é PTBR/data/mods/ptbr, com data/mods/ptbr na raiz do ZIP. Não existe build completo novo porque a tradução/revisão está pendente; a recusa foi testada.

## Preparação linguística

Leia briefing-do-jogo.md, formato-localizacao.md e fluxo-de-traducao.md. O briefing usa Steam e itch.io oficiais e fontes locais, cobrindo mundo procedural, sistemas, morte, fabricação e contexto. Glossário e diretrizes pertencem à tradução/revisão. As referências de 1.331 conversas estão disponíveis sem inferência de gênero.

## Execução

Após clone/pull em Ubuntu Server 24.04 ARM64, execute `python3 translation-work/toolkit.py doctor --arm64`. Se falhar, pare e envie o erro exato. Depois use status/resume, export-payload e apply. check valida trabalho parcial; build exige revisão completa. O preflight ARM64 não foi executado aqui.

## Publicação

O workflow verifica o build completo e publica automaticamente PTBR.zip, começando em v1.0.0 para o novo fluxo e incrementando patch somente se a saída mudar. As 19 tags antigas são preservadas por recibo. O cliente foi testado com HTTP simulado; Actions e publicação real não foram executados. Não houve commit ou push automático.

## Limites

Testes Windows e reconstrução técnica não comprovam apresentação dentro do jogo. Runtime, acentos, layout e compatibilidade de saves não foram testados. A conferência do Markdown bruto foi feita; não há alegação de preview renderizado. Consulte auditoria.md, requisitos.md e reports/acceptance.json para as evidências do aceite Windows e os limites de execução externa.
