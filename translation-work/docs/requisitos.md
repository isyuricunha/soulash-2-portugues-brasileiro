# Matriz de requisitos e evidências

| Área | Evidência | Situação |
|---|---|---|
| Repositório único e preservação privada | reference/migration.json, bundle e inventário ZIP | Migrado e verificado |
| Fontes nativas e batches | translations/manifest.json, reports/check.json | 5.987 fontes, 29.434 unidades, 59 lotes |
| Parser/reconstrução | reports/native-roundtrip.json e test_native_context.py | Corpus real e fixtures aprovados |
| Atualização incremental | test_project.py, reports/update-dry-run.json | Alteração, EN sobrescrito, no-op e fonte incompleta aprovados |
| Aplicação segura | test_project.py, test_atomic_apply.py | IDs, geração, campos imutáveis, sobrescrita e lote sujo aprovados |
| Armazenamento | test_contract.py, test_storage_guards.py, reports/scale-apply.txt | Retenção, recuperação, rollback e escala aprovados |
| Git e ARM64 | test_portability.py, test_doctor.py | Windows aprovado; execução ARM64 pendente do preflight |
| Releases | test_release_client.py, test_publishing.py, reports/publishing.txt | HTTP simulado e versões antigas aprovados |
| Licença/consentimento | LICENSE, permissões, test_consent.py | Texto integral e autorização explícita implementados |
| README | test_documents.py, reports/readme-links.json | Conteúdo conferido; render visual não realizado |
| Briefing e entrega | docs/briefing-do-jogo.md, fluxo e formato | Escritos com fontes e limites |

## Aceite da implementação Windows

A auditoria dos 29 itens de testes está em reports/requirements-map.json, com evidências por área e limitações do formato real. A suíte geral passou com 134 testes (um skip), complementada pelos testes específicos das últimas correções. A cópia isolada normalizada pelo Git passou no doctor. As variantes opcionais não se aplicam a este projeto.

A inspeção de Markdown bruto substituiu o preview porque nenhum renderer foi encontrado entre as ferramentas verificadas. A criação de symlink real foi pulada por privilégio; a recusa por atributo de filesystem foi testada. Esses limites estão registrados, sem alegação de execução inexistente.

Não há requisito de acessar servidor ARM64, instalar no jogo ou publicar uma Release ao vivo nesta implementação Windows. Esses resultados permanecem explicitamente não verificados.

Regressões adicionais aprovadas: falha de staging, três fronteiras de promoção e rollback interrompido com GC bloqueado. Descoberta sem Steam fornece fallback; metadados PT-BR são recusados como fonte original.

Contexto: 1.331 conversas cruzadas com entidades em reference/conversation-context.json, verificadas contra a fonte por test_context_reference.py. Enumeração de sexo permanece explicitamente desconhecida após busca em documentação e scripts locais; isso é um limite documentado da fonte, não uma decisão linguística presumida.

Autodetecção: instalação em cache única, cache conflitante com Steam, ausência de Steam, caminho com espaços, identidade errada e metadados traduzidos foram exercitados em fixtures. update --dry-run preservou todos os arquivos no teste. source-profiles.json agora fixa o inventário completo da versão aceita. update-sources recusa diferenças antes de sync; teste de instalação modificada aprovado. Versões novas podem ser importadas em uma operação com --accept-new-version após confirmação de que core_2 contém os originais; a confirmação e os hashes ficam no relatório. Perfis conhecidos continuam com comparação exata.

Inventário final: todos os caminhos do manifesto são relativos, sem travessia, existem em EN e correspondem aos source_file do catálogo (test_manifest_paths.py aprovado).


## Atualização de 01/11/2026

As contagens da migração inicial acima são históricas. Após excluir alinhamentos e sentinelas técnicas da extração, o corpus ativo contém 29.202 unidades em 59 lotes, todas preenchidas. Há 1.652 unidades revisadas e 27.550 aguardando revisão linguística. Foram recuperados 2.520 rascunhos com contexto alterado; eles não receberam aprovação automática. O mod legado perdeu 10 arquivos obsoletos e teve metadados técnicos restaurados. Consulte os relatórios em `../reports/`. O pacote final permanece bloqueado até a revisão integral; não houve teste dentro do jogo.
