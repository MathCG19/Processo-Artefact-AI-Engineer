# 1. Catálogo — violões até R$ 1.000

Consulta ao catálogo com filtro de categoria e preço, recomendação restrita ao que existe em estoque e tratamento de produto esgotado (sugestão de alternativas, seção 7.3 do manual).

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0040 · As linhas **Ferramentas** mostram o que o agente consultou (não aparecem para o cliente).

---

**Cliente:** Oi! Tô começando a aprender violão. Quais opções vocês têm até R$ 1.000?

> **Ferramentas:** `search_products(category='Violões', max_price=1000)`

**Duda:**

Oi! Que legal começar a tocar violão. Temos 12 opções disponíveis até R$ 1.000:

- Tagima Memphis AC-39 Nylon Natural: R$ 429,90
- Rozini RC-104 Nylon Estudante: R$ 459,90
- Shelby SN-100 Folk Aço Preto: R$ 549,00
- Giannini GF-1R Aço Folk Sunburst: R$ 579,90
- Yamaha C40 Nylon Natural: R$ 599,90
- Giannini GN-15 Nylon Cedro Natural: R$ 689,00
- Yamaha F310 Aço Natural: R$ 699,90
- Tagima Dallas Tuner Aço Natural: R$ 749,00
- Shelby SGD-195E Elétrico Aço Sunburst: R$ 799,00
- Yamaha C70 Nylon Natural: R$ 849,00
- Tagima Woodstock Dreadnought Natural: R$ 899,00
- Tagima TW-7 7 Cordas Aço Natural: R$ 999,00

Para quem está começando, eu olharia para os de cordas de nylon, como o Yamaha C40 ou o Rozini RC-104 Estudante. As cordas são mais macias nos dedos, o que facilita muito nas primeiras semanas. Os de aço têm um som mais brilhante e projetam mais, mas doem mais no início. O Yamaha F310, de aço, é uma escolha muito popular se você preferir esse som.

Quer que eu veja detalhes de algum deles?

---

**Cliente:** Prefiro corda de nylon. Qual você recomenda pra quem tá começando?

**Duda:**

Pra quem está começando com nylon, eu escolheria o **Yamaha C40 Nylon Natural**, por R$ 599,90. A Yamaha é uma marca muito conhecida pela qualidade e pela durabilidade, e esse modelo é um clássico de entrada. Ele tem bom acabamento e afinação estável, o que ajuda quando a gente ainda está aprendendo a afinar.

Se o orçamento estiver mais apertado, o **Rozini RC-104 Nylon Estudante** (R$ 459,90) também é uma opção que faz sentido para estudar. E se quiser gastar um pouco mais, o **Yamaha C70** (R$ 849,00) é um degrau acima, com acabamento melhor.

Quer que eu confira os detalhes de algum deles?

---

**Cliente:** E o Giannini GF-3D, vocês têm?

> **Ferramentas:** `search_products(query='Giannini GF-3D', include_unavailable=True)`

**Duda:**

O Giannini GF-3D Dreadnought Sunburst está esgotado no momento, mas volta a ser uma opção depois que a equipe repor o estoque.

Como você prefere nylon, eu seguiria com o **Yamaha C40 Nylon Natural** (R$ 599,90) ou o **Rozini RC-104 Nylon Estudante** (R$ 459,90). Se quiser um violão de aço parecido com o GF-3D, o **Giannini GF-1R Aço Folk Sunburst** (R$ 579,90) é da mesma marca e está disponível.

Quer que eu confira os detalhes de algum desses?

---
