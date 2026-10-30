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

## Casos ainda não comprovados integralmente

A aceitação final permanece aberta até revisar cada subitem de testes do anexo. Ainda é necessário ampliar a prova para inspecionar a apresentação renderizada quando houver ferramenta disponível. O teste de symlink real foi pulado por privilégio do Windows. Não converter essas lacunas em aprovação por ausência de falhas.

Não há requisito de acessar servidor ARM64, instalar no jogo ou publicar uma Release ao vivo nesta implementação Windows. Esses resultados permanecem explicitamente não verificados.

Regressões adicionais aprovadas: falha de staging, três fronteiras de promoção e rollback interrompido com GC bloqueado. Descoberta sem Steam fornece fallback; metadados PT-BR são recusados como fonte original.

Contexto: 1.331 conversas cruzadas com entidades em reference/conversation-context.json, verificadas contra a fonte por test_context_reference.py. Enumeração de sexo permanece explicitamente desconhecida após busca em documentação e scripts locais; isso é um limite documentado da fonte, não uma decisão linguística presumida.

Autodetecção: instalação em cache única, cache conflitante com Steam, ausência de Steam, caminho com espaços, identidade errada e metadados traduzidos foram exercitados em fixtures. update --dry-run preservou todos os arquivos no teste. source-profiles.json agora fixa o inventário completo da versão aceita. update-sources recusa diferenças antes de sync; teste de instalação modificada aprovado. Versões novas exigem revisão explícita dos originais e do perfil.

Inventário final: todos os caminhos do manifesto são relativos, sem travessia, existem em EN e correspondem aos source_file do catálogo (test_manifest_paths.py aprovado).
