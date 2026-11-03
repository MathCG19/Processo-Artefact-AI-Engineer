# 2. Preço, promoção e formas de pagamento

Combina dado estruturado (preço, promoção ativa) com regra da política (PIX, parcelamento, promoções não cumulativas — seções 3, 3.1 e 6.2).

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0046 · As linhas **Ferramentas** mostram o que o agente consultou (não aparecem para o cliente).

---

**Cliente:** Quanto custa o Takamine GD20?

> **Ferramentas:** `search_products(query='Takamine GD20')`

**Duda:**

Oi! O Takamine GD20 Dreadnought Natural está disponível por R$ 2.199,00, sem promoção no momento. Temos 5 unidades em estoque.

Quer que eu traga mais detalhes sobre ele ou compare com outros violões?

---

**Cliente:** E no PIX? Dá pra parcelar no cartão também?

> **Ferramentas:** `search_store_policies(query='desconto no PIX e parcelamento no cartão de crédito', k=5)`

**Duda:**

No PIX, você paga R$ 2.089,05 à vista (5% de desconto sobre R$ 2.199,00). Esse desconto não é cumulativo com promoções, mas este violão está sem promoção, então vale.

No cartão de crédito, dá para parcelar em até 12x sem juros, com parcela mínima de R$ 100,00. Assim, as 12 parcelas ficam em R$ 183,25.

Quer que eu veja mais alguma coisa sobre o GD20?

---

**Cliente:** E o Taylor 110e, tá com algum desconto?

> **Ferramentas:** `search_products(query='Taylor 110e')`

**Duda:**

Sim! O Taylor 110e Dreadnought Natural está em promoção "Desconto Exclusivo", com 8% de desconto:

- Preço original: R$ 5.999,00
- Preço final: R$ 5.519,08

Ele está disponível, com 4 unidades em estoque.

Quer que eu compare com o GD20 ou mostre outras opções?

---

**Cliente:** Se eu pagar o Taylor no PIX ganho os 5% em cima do desconto?

**Duda:**

Não, o desconto de PIX não se soma à promoção. As promoções não são cumulativas, então o desconto de 5% no PIX não se aplica sobre um preço que já está em promoção.

No PIX, o Taylor fica em R$ 5.519,08, que é o mesmo preço final da promoção. No cartão, dá para parcelar em até 12x sem juros, com parcela mínima de R$ 100,00.

Quer que eu veja mais alguma coisa sobre os dois violões?

---
