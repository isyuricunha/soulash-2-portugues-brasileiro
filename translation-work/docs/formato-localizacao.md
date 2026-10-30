# Formato e identidade

JSON UTF-8 é reconstruído preservando todos os campos técnicos do original. TXT de nomes próprios é preservado byte a byte. A seleção de campos está em extractor.py. Arquivos de scripts, mapas, imagens e registros técnicos não são copiados para EN.

Cada unidade usa caminho relativo e endereço semântico. Listas de objetos com id usam esse id e ocorrência; listas sem id usam hash do valor e ocorrência. Esse fallback não permite reconhecer uma edição como a mesma unidade: resulta em remoção e adição, sem reutilização por similaridade. Reordenação de objetos com id preserva identidade. Contexto relevante alterado invalida a tradução conservadoramente.

pointer indica o endereço atual; destination indica o campo reconstruído. Unidades sintéticas de feminine_affix permitem revisão explícita da concordância. gender se aplica ao nome de entidade e aceita masculine ou feminine. reviewed é uma aprovação explícita, nunca inferida de PTBR preenchido.

O contexto preserva seletores e IDs ancestrais. Os valores de npc_sex e player_sex são evidência bruta, não enumerações interpretadas. Nomes não comprovam gênero. EN/data/mods/core_2 espelha o caminho original; PTBR/data/mods/ptbr espelha o destino de instalação.


## Referências de conversa

reference/conversation-context.json cruza 1.331 registros de conversa com os IDs de entidades da fonte aceita. Cada registro conserva IDs, caminhos e nomes originais das entidades, tipo, opções e valores brutos de npc_sex/player_sex. Múltiplas correspondências permanecem explícitas. Consulte esse catálogo junto à entrada JSONL e às opções vizinhas; nomes e IDs indicam contexto, não confirmam gênero gramatical.

A documentação local e os scripts consultados não definiram a enumeração numérica de sexo. Por isso ela não é interpretada automaticamente. Falas em dialogues.json podem alternar participantes e mencionar terceiros; posição da linha e sexo de um participante não autorizam atribuir a concordância a todos os referentes. As formas femininas de itens são escolhas de localização, independentes dessas identidades.
