# 2. Preço, promoção e formas de pagamento

Combina dado estruturado (preço, promoção ativa) com regra da política (PIX, parcelamento, promoções não cumulativas — seções 3, 3.1 e 6.2).

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0045 · As linhas 🔧 mostram as ferramentas que o agente chamou (não aparecem para o cliente).

---

**👤 Cliente:** Quanto custa o Takamine GD20?

> 🔧 `search_products(query='Takamine GD20')`

**🎸 Duda:**

Oi! O Takamine GD20 Dreadnought Natural está por **R$ 2.199,00**, sem promoção no momento, e está disponível em estoque (5 unidades).

Quer que eu traga mais detalhes sobre ele ou de algum outro violão?

---

**👤 Cliente:** E no PIX? Dá pra parcelar no cartão também?

> 🔧 `search_store_policies(query='desconto no PIX e parcelamento no cartão de crédito', k=5)`

**🎸 Duda:**

No PIX, você tem **5% de desconto**. Como o Takamine GD20 não está em promoção, o desconto incide sobre o preço de R$ 2.199,00, ficando em **R$ 2.089,05**.

No cartão de crédito, dá para parcelar **em até 12x sem juros**, com parcela mínima de R$ 100,00. Assim, o violão sai em 12x de R$ 183,25.

Também é possível combinar PIX com cartão em compras acima de R$ 2.000,00, caso queira.

---

**👤 Cliente:** E o Taylor 110e, tá com algum desconto?

> 🔧 `search_products(query='Taylor 110e')`

**🎸 Duda:**

Sim! O Taylor 110e Dreadnought Natural está em promoção **Desconto Exclusivo de 8%**:

- De R$ 5.999,00 por **R$ 5.519,08**
- Disponível, com 4 unidades em estoque

Como as promoções não são cumulativas, o desconto de 5% no PIX não se aplica sobre esse preço promocional. No cartão, o parcelamento em até 12x sem juros continua valendo.

---

**👤 Cliente:** Se eu pagar o Taylor no PIX ganho os 5% em cima do desconto?

**🎸 Duda:**

Não, infelizmente não. A política da loja diz que as promoções não são cumulativas, então o desconto de 5% no PIX não se aplica sobre um preço que já está em promoção.

Então o Taylor 110e sai por **R$ 5.519,08** tanto no PIX quanto no cartão. A diferença é que no cartão você pode parcelar em até 12x sem juros.

Quer que eu veja mais alguma coisa para você?

---
