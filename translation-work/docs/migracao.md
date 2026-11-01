# Consolidação do repositório privado

O snapshot completo dos arquivos não secretos está em reference/private-worktree.zip. O inventário com SHA-256 por arquivo está em reference/private-worktree-manifest.json; migration.json registra origem e hash do arquivo. O ZIP foi lido integralmente e comparado ao inventário. Ele conserva fontes 0.10.1, tradução original, testes e implementação anterior para consulta, sem executar provedores.

O histórico Git completo está em reference/private-history.bundle, verificado com git bundle verify. Para recuperar em outro diretório: `git clone translation-work/reference/private-history.bundle destino`. O bundle preserva commits e referências; não altera o histórico deste repositório.

O fluxo ativo usa somente translation-work/toolkit.py. Código de provedores arquivado é histórico, não dependência executada. Traduções compatíveis com a fonte atual são reaproveitadas sem aprovação linguística automática. Arquivos antigos públicos permanecem preservados; os pacotes antigos não são entradas do novo workflow.

A instalação do jogo e o diretório privado não foram modificados. Não inclua credenciais em novos arquivos ou commits.

## Fonte pública anterior

A tradução pública antiga também é comparada às pendências após o reaproveitamento privado. Somente unidades com mesma identidade, inglês e contexto podem preencher células vazias, com validação de marcadores e origem registrada. O relatório reports/public-reuse.json lista o resultado. Nenhuma aprovação linguística é inferida dessa recuperação.

Resultado da comparação pública: nenhuma unidade adicional satisfez simultaneamente identidade, fonte e contexto compatíveis entre as pendências. Nenhum texto foi descartado: a árvore pública antiga permanece no repositório e o privado está arquivado integralmente. O corpus ativo mantém 25.249 traduções recuperadas e 4.185 entradas vazias.


## Atualização de 01/11/2026

As contagens da migração inicial acima são históricas. Após excluir alinhamentos e sentinelas técnicas da extração, o corpus ativo contém 29.202 unidades em 59 lotes, todas preenchidas. Há 1.652 unidades revisadas e 27.550 aguardando revisão linguística. Foram recuperados 2.520 rascunhos com contexto alterado; eles não receberam aprovação automática. O mod legado perdeu 10 arquivos obsoletos e teve metadados técnicos restaurados. Consulte os relatórios em `../reports/`. O pacote final permanece bloqueado até a revisão integral; não houve teste dentro do jogo.
