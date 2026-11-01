# Fluxo de trabalho

1. Após clone/pull no Ubuntu ARM64, execute `python3 translation-work/toolkit.py doctor --arm64`. Se falhar, pare e encaminhe o erro exato. Não instale dependências ou altere hashes para contornar o erro.
2. Leia briefing-do-jogo.md e formato-localizacao.md. Mantenha glossario-ptbr.md e diretrizes-de-traducao.md como decisões linguísticas próprias.
3. Execute status ou resume e consulte diff. Leia os lotes JSONL em grupos pequenos. Traduções migradas permanecem sem aprovação.
4. Aplique somente campos editáveis com apply --payload arquivo.json. O envelope contém generation, expected_count e entries; cada entrada contém id, source_fingerprint, PTBR e, quando necessário, gender e reviewed. Use native.fingerprint para obter a impressão da fonte. --replace autoriza substituir PTBR já preenchido após revisão.
5. Execute check. Quando tudo estiver traduzido e revisado, execute build, verify-output e package. O ZIP gerado em translation-work/.state/PTBR.zip contém data/mods/ptbr na raiz.
6. Após revisão das alterações e push pelo mantenedor, o workflow publica automaticamente apenas o pacote completo. Commits apenas de lotes não publicam.

Atualizações: update-sources tenta Steam ou caminho local previamente verificado; use --game-root para caminho explícito. --dry-run não grava. sync lê EN já atualizado ou --source-root. Fontes alteradas mantêm PTBR antigo no histórico e ficam pendentes. Arquivos ausentes bloqueiam a operação para impedir importação parcial.

Recuperação: recover restaura transações interrompidas; --break-lock só funciona se o processo anterior terminou. rollback reverte a última operação compatível. gc --dry-run mostra snapshots elegíveis; gc elimina somente transações concluídas elegíveis. Retenção padrão: 10 snapshots e 512 MiB, preservando recuperação pendente. Configure retention em config.json para count, budget e headroom. Git preserva histórico durável somente após commits feitos pelo mantenedor.


## Exemplo de aplicação

```json
{"generation":"copie o valor de status","expected_count":1,"entries":[{"id":"ID da entrada","source_fingerprint":"SHA-256 obtido com native.fingerprint","PTBR":"texto revisado","reviewed":true}]}
```

Use apenas texto nativo em PTBR, mantendo as variáveis originais. Não use tokens artificiais __KEEP_. Uma entidade exige também gender; revisões podem preencher PTBR sem marcar reviewed até a conferência final. Rejeições são retornadas com ID e motivo; entradas válidas do mesmo payload são salvas.

## Recuperar o arquivo privado

`git clone translation-work/reference/private-history.bundle destino` recupera o histórico em outro diretório. O snapshot private-worktree.zip pode ser extraído em um diretório separado para consulta; não sobreponha o fluxo ativo com a implementação antiga. Os arquivos de preservação não entram em PTBR.zip.

## Procedência das fontes

Para versões conhecidas, update-sources exige o inventário SHA-256 de source-profiles.json ou do último manifesto aceito. Uma instalação 0.10.5 modificada é recusada antes de sincronizar. Para uma nova versão original, use update-sources --game-root "/path/to/Soulash 2" --accept-new-version --dry-run para inspecionar e repita sem --dry-run para importar. A opção afirma explicitamente que os arquivos são originais e não modificados; não representa assinatura do publicador. Ela não autoriza diferenças de uma versão conhecida, nem downgrade. Não regenere hashes para silenciar diferenças. sync continua disponível para reconciliação explícita de fontes fornecidas pelo mantenedor, com histórico e diffs.

Para obter o envelope com IDs e fingerprints sem calculá-los manualmente: `python translation-work/toolkit.py export-payload > payload.json`. Recorte entries para o grupo que será trabalhado e ajuste expected_count. O comando é somente leitura; não preenche nem aprova traduções.

O histórico versionado de sync guarda inventário anterior e apenas unidades alteradas/removidas, evitando duplicar o catálogo inteiro a cada atualização. O catálogo ativo e as unidades anteriores alteradas permitem recompor os valores aceitos; backups locais de bytes são temporários e limitados, enquanto Git fornece o histórico durável após commit.
