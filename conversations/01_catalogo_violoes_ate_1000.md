# 1. Catálogo — violões até R$ 1.000

Consulta ao catálogo com filtro de categoria e preço, recomendação restrita ao que existe em estoque e tratamento de produto esgotado (sugestão de alternativas, seção 7.3 do manual).

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0038 · As linhas 🔧 mostram as ferramentas que o agente chamou (não aparecem para o cliente).

---

**👤 Cliente:** Oi! Tô começando a aprender violão. Quais opções vocês têm até R$ 1.000?

> 🔧 `search_products(category='Violões', max_price=1000)`

**🎸 Duda:**

Oi! Que bom saber que você está começando. Temos 12 violões até R$ 1.000, todos disponíveis:

- **Tagima Memphis AC-39 Nylon Natural**: R$ 429,90
- **Rozini RC-104 Nylon Estudante**: R$ 459,90
- **Shelby SN-100 Folk Aço Preto**: R$ 549,00
- **Giannini GF-1R Aço Folk Sunburst**: R$ 579,90
- **Yamaha C40 Nylon Natural**: R$ 599,90
- **Giannini GN-15 Nylon Cedr Natural**: R$ 689,00
- **Yamaha F310 Aço Natural**: R$ 699,90
- **Tagima Dallas Tuner Aço Natural**: R$ 749,00
- **Shelby SGD-195E Elétrico Aço Sunburst**: R$ 799,00
- **Yamaha C70 Nylon Natural**: R$ 849,00
- **Tagima Woodstock Dreadnought Natural**: R$ 899,00
- **Tagima TW-7 7 Cordas Aço Natural**: R$ 999,00

Para quem está começando, eu olharia primeiro os de **cordas de nylon**: as cordas são mais macias e doem menos nos dedos no início. A **Yamaha C40** é uma escolha clássica de estudo. Se você prefere som mais brilhante e cordas de aço, a **Yamaha F310** é muito citada para iniciantes.

Quer que eu detalhe algum deles?

---

**👤 Cliente:** Prefiro corda de nylon. Qual você recomenda pra quem tá começando?

**🎸 Duda:**

Pra quem está começando com nylon, eu iria de **Yamaha C40 Nylon Natural (R$ 599,90)**. É um violão de estudo muito usado, com boa afinação e acabamento, e costuma ser o que professores indicam para o primeiro instrumento. Ela também já é de uma marca conhecida, o que ajuda se você quiser trocar cordas ou fazer manutenção depois.

Se o orçamento estiver mais apertado, o **Tagima Memphis AC-39 (R$ 429,90)** é a opção mais barata nesse estilo. Se quiser ir um pouco além, o **Yamaha C70 (R$ 849,00)** é um degrau acima, com mais acabamento.

Quer que eu veja mais detalhes de algum deles?

---

**👤 Cliente:** E o Giannini GF-3D, vocês têm?

> 🔧 `search_products(query='Giannini GF-3D', include_unavailable=True)`

**🎸 Duda:**

Infelizmente o **Giannini GF-3D Dreadnought Sunburst** (R$ 799,90) está esgotado no momento, então não consigo garantir a compra agora.

Se quiser uma alternativa parecida, temos disponíveis:

- **Giannini GN-15 Nylon Cedr Natural** (R$ 689,00), da mesma marca, com cordas de nylon
- **Yamaha C40 Nylon Natural** (R$ 599,90), a minha indicação para quem está começando com nylon

Quer que eu veja mais detalhes de algum deles?

---
