# Publicação automática

O workflow .github/workflows/auto-release.yml roda em alterações de PTBR ou build-manifest na branch main e por disparo manual. Commits só de tradução, README ou documentação não publicam. A permissão é contents: write e a concorrência é serializada.

O primeiro build completo deste fluxo usa v1.0.0. Saída nativa diferente incrementa patch; saída idêntica não cria versão. A tag aponta para o commit exato. O cliente confirma a branch padrão atual antes de publicar, verifica ancestrais e recusa conflitos. Drafts interrompidos só são retomados se commit e fingerprint coincidirem.

Apenas PTBR.zip é permitido como asset. O ZIP contém data/mods/ptbr na raiz e não inclui EN, lotes, manifestos, licenças do repositório ou arquivos de arquivo privado. As notas incluem mudanças por categoria, compatibilidade, instalação, comparação, créditos e comunidade. Nenhum teste simulado publicou uma Release real.

## Conferência após o push pelo mantenedor

Após revisão completa e build, commit do PTBR e build-manifest deve incluir as fontes e lotes correspondentes. O workflow verifica a saída sem reconstruir o nativo e publica o ZIP. Acompanhe a execução em Actions; confirme tag, notas, único asset e instalação. Se falhar, preserve o erro e o draft; não retague nem apague Releases públicas automaticamente.

O comando de teste é `python -m unittest discover -s translation-work/tests -p test_publishing.py -v`. O transporte HTTP é simulado, mas executa o cliente usado em produção e seus endpoints. Execução real do GitHub Actions e publicação real permanecem não verificadas.

As 19 tags históricas v0.0.1 a v0.0.19 estão registradas por commit em legacy-releases.json e protegidas pela integridade da toolchain. O cliente confirma seus commits e ancestralidade, preserva as publicações antigas e inicia a série da toolkit em v1.0.0. Tags desconhecidas sem manifesto, tags alteradas e históricos divergentes falham; nenhuma versão antiga é apagada ou retagueada.
