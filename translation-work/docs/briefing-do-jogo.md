# Briefing de Soulash 2

Pesquisa técnica e contextual em 30/10/2026. Este documento fornece contexto; as escolhas de PT-BR pertencem à revisão linguística.

## Mundo e narrativa

Soulash 2 combina RPG sandbox, roguelike tradicional e simulação histórica. A premissa oficial situa o mundo após a queda dos deuses e uma destruição seguida de renascimento. O personagem não segue uma biografia fixa: a geração procedural e as ações do jogador produzem histórias próprias. Não atribua aos NPCs uma história universal nem trate nomes gerados como personagens canônicos.

Assentamentos, famílias, comércio e guerras participam da história simulada, antes e durante a aventura. Uma conversa pode mencionar parentes, ocupações, relações políticas ou locais que dependem do mundo gerado. As variáveis devem continuar representando essas informações; o texto não deve fixar gênero, parentesco ou identidade que a fonte deixa dinâmicos.

## Sistemas e contexto dos textos

A progressão ocorre pelo uso de habilidades, sem uma classe fixa obrigatória. Exploração, combate por turnos, criação de equipamentos, comércio, construção e conquista coexistem. Diferencie nomes curtos de ações, descrições de efeitos mecânicos, falas e eventos históricos: cada contexto tem limites próprios de tamanho e registro.

A fabricação usa materiais como base e ingredientes especiais para propriedades adicionais. O nome de uma entidade pode ser combinado com um afixo de recurso. Por isso o gênero gramatical do item traduzido e a forma feminina do afixo são dados de localização relevantes; não são prova do sexo de um personagem.

O jogador pode construir casas e oficinas, organizar produção, atrair famílias, formar exércitos e conquistar assentamentos. O legado pode continuar por descendentes. Não reduza todos os termos de administração a combate: estoque, salários, profissões, caravanas e relações familiares descrevem sistemas diferentes.

## Morte e continuidade

A página oficial no itch.io descreve High Fantasy (ressurreição com penalidades em local amistoso), Dark Fantasy (perda do personagem com persistência do mundo) e Hardcore (perda do personagem e mundo). A descrição de cada modo deve conservar exatamente as consequências apresentadas na fonte atual. Não prometa compatibilidade de saves nem ausência de perda.

## Povos, regiões e personagens

O conteúdo é procedural; não há uma lista única de facções e governantes para todos os mundos. Os recursos locais contêm entidades e NPCs, regiões e padrões de nomes. Use seus IDs e referências cruzadas para distinguir espécie, profissão, pessoa e objeto. A apresentação oficial menciona necromancia e o Necrotyrant nas terras geladas do norte; isso fornece contexto de fantasia, sem autorizar inventar relações ou história adicional.

Os arquivos conversations.json expõem entidades elegíveis, IDs, npc_sex e player_sex em algumas conversas. Esses campos referem-se a participantes diferentes. O valor numérico é preservado como evidência bruta: sua enumeração não foi comprovada pelo código do motor. Uma fala com npc_sex não determina o gênero da pessoa descrita nela. Não deduza gênero apenas pelo nome.

## Orientações para investigação linguística

Leia as entradas vizinhas e as referências das opções de conversa. Diferencie texto dito pelo NPC, resposta do jogador e mensagem do sistema. Preserve ::variaveis, substituições entre chaves, printf, marcação de cor, números e quebras. Confira concordância em nomes montados e afixos. Registre decisões de terminologia no glossário e de registro nas diretrizes; este briefing não aprova traduções.

## Fontes e limites

- [Steam oficial](https://store.steampowered.com/app/2399160/Soulash_2/): identidade, Artur Smiarowski como desenvolvedor/publicador, premissa e sistemas. Consultada em 30/10/2026.
- [Página oficial no itch.io](https://wizardsofthecode.itch.io/soulash-2): geração histórica, fabricação e modos de morte. Consultada em 30/10/2026.
- [Devlog oficial v0.7.3](https://wizardsofthecode.itch.io/soulash-2/devlog/705328/soulash-2-v073-stability): adoção de UTF-8 e suporte a caracteres europeus; não comprova renderização de todos os textos deste pacote.
- Recursos locais da versão 0.10.5: data/mods/core_2/conversations.json, entities/, npc/, locations.json e changelog.txt. O changelog registra formas femininas e neutras para nomes e afixos de entidades.

A versão analisada é 0.10.5 conforme version.txt local. As páginas externas podem descrever versões diferentes. Não houve teste dentro do jogo. O motor usa SDL conforme a página oficial; não há dependência de ferramentas de extração Unity ou de executáveis externos nesta toolkit.
