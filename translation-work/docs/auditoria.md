# Auditoria de entrega

## Evidências disponíveis

- Fontes reais 0.10.5 importadas e check profundo aprovado: reports/check.json.
- Atualização real sem mudanças: reports/update-dry-run.json.
- Build real incompleto recusado: reports/build-attempt.txt.
- Histórico privado completo: bundle verificado; snapshot de 11.547 arquivos verificado por SHA-256.
- Testes de projeto: extração, lotes, sync de EN sobrescrito, idempotência, aplicação parcial, fontes alteradas, build/ZIP e recusa de saída adulterada.
- Testes de armazenamento: 500 alterações, retenção, rollback, recuperação, orçamento e recibos corrompidos.
- Testes de publicação: HTTP real do cliente com transporte simulado, primeira versão, patch, repetição, rascunho interrompido, commit antigo, conflito de tag, anexos extras e README sem incremento.
- Normalização pelo índice Git, alteração semântica e alteração binária verificadas.

## Limites e itens ainda em auditoria

A suíte consolidada inicial passou com 31 testes. A regressão adicional via Project.apply passou com 500 payloads em 101 lotes, preservando o lote não alterado e os limites de retenção (reports/scale-apply.txt). A reconstrução do corpus real passou em 5.987 arquivos e 29.434 unidades (reports/native-roundtrip.json). Testes adicionais de descoberta, contexto, consentimento e publicação constam nos respectivos testes. A auditoria completa do anexo ainda precisa ser finalizada; inspeção visual renderizada não foi realizada por ausência de renderer no ambiente verificado.

Ubuntu ARM64: execução real pendente do preflight após clone/pull. Jogo: execução e renderização não testadas. GitHub: publicação e Actions ao vivo não executados. Esses testes externos não são substituídos por mocks.

Suíte consolidada inicial: 31 testes aprovados em 196,752 s. Testes adicionais posteriores têm seus resultados registrados durante a auditoria. Renderizadores Markdown não estavam disponíveis no ambiente Python; o Markdown bruto, links e limites de imagens foram verificados, sem alegação de inspeção visual renderizada.

Segurança de caminhos: travessia e caminhos absolutos foram recusados em testes. O teste de symlink real foi pulado porque o Windows não concedeu privilégio de criação; a recusa está implementada, mas esse caso não foi comprovado ao vivo. Sobrescrita acidental de PTBR e fonte nova não aceita também têm regressões aprovadas.

Verificação de links: a arte oficial retornou HTTP 200 anteriormente. Shields e os destinos de comunidade/portal retornaram 403 neste ambiente; não foi inferido que os destinos estão mortos. As imagens de badges foram substituídas por links acessíveis comuns, conforme o fallback do anexo; os destinos fornecidos pelo mantenedor foram preservados.

Migração de versões históricas: 19 tags registradas com SHA de commit, verificadas no fluxo de publicação. Regressão com Release antiga preservada e primeira Release da toolkit em v1.0.0 passou; suíte de publicação: 19 testes em 17,549 s.

Perfil de origem reforçado: instalação real 0.10.5 aprovada sem mudanças em reports/update-profile-dry-run.json. Workflows de Release e consentimento têm regressões de ligação aprovadas. A proteção de symlink foi exercitada com atributo de filesystem simulado; criação de link real continua não verificada por privilégio.

Revisão editorial do publicador encontrou e corrigiu mojibake nas notas de Release. Regressão de UTF-8 adicionada e aprovada; suíte HTTP/publicação reexecutada com sucesso após a correção.

Regressões de apresentação: diálogos, múltiplas categorias, categoria desconhecida, primeira Release e alteração somente nativa aprovadas em test_changelog.py. Download antecede Pix, comparação e comunidade estão presentes. Rebuild incompleto preserva byte a byte a saída anterior em test_project.py.

Regressões finais adicionadas: texto público rejeita personas e narração do mantenedor em terceira pessoa, aceitando créditos concisos; cadeia engine-shapes → toolchain → runtime foi exercitada em fixture com normalização e adulteração.

A revisão UTF-8 foi ampliada aos módulos ativos. Metadados do idioma e relatórios foram corrigidos; regressões conferem ausência de mojibake e o rótulo nativo Português Brasileiro. Traduções JSONL preservadas.

A preservação privada agora tem regressões permanentes: test_migration.py valida todos os membros e hashes do ZIP e executa git bundle verify. Ambos aprovados.

Histórico incremental de sync reduzido a inventário anterior e unidades alteradas/removidas; não duplica o catálogo completo por atualização. Regressão de histórico anterior passou após a mudança.

Remoção de unidade e adição de novo arquivo nativo têm regressões aprovadas: removidos saem do conjunto ativo com histórico; arquivo novo não invalida traduções existentes. Suíte do fluxo: 15 testes aprovados após essas adições.

Catálogo: alterações em EN imutável e duplicação de registro JSONL são recusadas por regressões. CLI --help funciona fora do cwd do projeto; build --dry-run é explicitamente recusado. Suíte do fluxo ampliada: 17 testes aprovados.

A árvore de imports do fluxo ativo foi verificada em test_no_network_toolkit.py: não há cliente de tradução, provedor ou biblioteca HTTP na extração, aplicação, sync ou build. O HTTP permanece isolado no publicador de Releases.

Formato nativo: gênero feminino de entidade e feminine_affix reconstruídos em fixture sem alterar dano/IDs. Marcações de cor quebradas e números alterados são recusados; casos aprovados em test_native_context.py e test_contract.py.

## Resultado consolidado observado em 01/11/2026

A execução em reports/tests-final-windows.txt terminou com 95 testes em 642,148 s: OK, um skip por privilégio de symlink real. A execução começou antes de algumas alterações posteriores; os módulos alterados tiveram verificações específicas, mas a suíte precisa ser repetida sobre a versão final antes do aceite.

A revisão identificou duas pendências funcionais: update-sources para versões futuras ainda depende de edição de perfil pelo desenvolvimento, e o catálogo externo de contexto precisa ser atualizado/invalidado de forma consistente após sync. Esses itens serão corrigidos antes da conclusão; não são bloqueios externos.

## Importador: ordem de confiança

update-sources verifica os recibos da toolkit antes de consultar a instalação e o perfil. Regressão específica confirma ausência de acesso às fontes em caso de CHECKSUM_MISMATCH; oito testes de descoberta aprovados.

Versões futuras: --accept-new-version permite atualização em uma operação após confirmação explícita de origem pelo mantenedor, registrada no relatório transacional com fingerprint. Versões conhecidas alteradas continuam recusadas; dry-run não grava. Não é alegada autenticação criptográfica do publicador. Regressão de versão 0.10.6 aprovada.

Correção de reordenação: o fingerprint semântico deixa de incluir posições de arrays do contexto. A sincronização de duas conversas reordenadas preservou revisão e PTBR, reportou dois movimentos e zero modificações. O manifesto aceito permite repetir importação de versão futura sem nova confirmação.

## Correção da inclusão no Git

A regra histórica *.py ignorava o código da toolkit e os testes. Exceções explícitas em .gitignore agora incluem translation-work/*.py e translation-work/tests/*.py. Regressão verifica git check-ignore para CLI, adaptador, publicador e testes. O mantenedor deve incluir esses arquivos no próximo commit; não foi criado commit automaticamente.


## Aceite final — implementação Windows e migração

Resultado geral: 134 testes em 788,765 s, OK (um skip de symlink real). As últimas alterações têm resultados específicos adicionais: 21 testes de fluxo, 10 de descoberta, 3 de workflows/inclusão Git, 2 de migração e 5 de documentos aprovados. A matriz de 29 requisitos está em reports/requirements-map.json. Notas anteriores deste documento descrevem etapas históricas da auditoria; este aceite e reports/acceptance.json representam o estado final.

A importação de versões futuras foi resolvida por confirmação explícita de originais, sem editar a implementação; perfis conhecidos e manifesto aceito continuam protegidos por hashes. O catálogo externo de contexto é invalidado transacionalmente quando a geração muda, e o contexto ativo dos JSONL permanece atualizado. O histórico incremental permite reconstruir o catálogo anterior, incluindo adições, remoções e movimentos, sem snapshots integrais repetidos.

A regra Git histórica que ignorava Python foi corrigida. O doctor passou na cópia isolada extraída de uma árvore Git produzida com índice temporário; o índice real do mantenedor não foi alterado. O código da toolkit e os testes devem ser incluídos no próximo commit. Nenhum commit, push, instalação no jogo ou Release real foi feito nesta entrega.

Permanecem deliberadamente não executados: preflight no Ubuntu ARM64 do destino, testes dentro do jogo e GitHub Actions/publicação ao vivo. O anexo permite concluir o trabalho Windows com essas limitações explícitas. A tradução linguística continua pendente; não há PTBR novo incompleto nem alegação de tradução finalizada.
