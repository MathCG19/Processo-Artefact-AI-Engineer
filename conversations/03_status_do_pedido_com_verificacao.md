# 3. Status do pedido com verificação de identidade (não trivial)

Cliente anônimo: o agente exige número do pedido + contato antes de consultar (a checagem é feita pela ferramenta, não pelo prompt), detecta o atraso calculado em código e registra um chamado com protocolo para a equipe.

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0033 · As linhas **Ferramentas** mostram o que o agente consultou (não aparecem para o cliente).

---

**Cliente:** Oi, meu pedido ainda não chegou. É o número 8.

**Duda:**

Oi! Sinto muito pela demora. Para eu consultar o pedido 8, me passa também o e-mail ou o telefone usado na compra. Assim consigo verificar o status e a previsão de entrega.

---

**Cliente:** anacarol.ferreira@coldmail.com

> **Ferramentas:** `get_order_status(order_id=8, contact='anacarol.ferreira@coldmail.com')` → `search_store_policies(query='prazo de entrega atrasado o que fazer pedido não chegou')`

**Duda:**

Ana, encontrei o pedido 8: um Kala KA-C Concert Mogno, no valor de R$ 349,90, pago no cartão de débito.

O status é "enviado, em transporte". A previsão de entrega era 28/02/2026, então o pedido está atrasado em 248 dias. O código de rastreio é BRJL5544332BR, se quiser acompanhar pelos Correios ou pela transportadora.

Como o prazo já passou há bastante tempo, sugiro registrar o caso para a equipe verificar o que aconteceu com a entrega. Quer que eu abra esse registro agora?

---

**Cliente:** Nossa, tá muito atrasado! O que vocês podem fazer?

**Duda:**

Sinto muito pela situação, Ana. Um pedido com mais de oito meses de atraso merece atenção.

Eu não consigo alterar a entrega nem resolver isso por aqui. O que posso fazer é registrar uma reclamação para a equipe humana, que vai investigar o envio com a transportadora. Pela nossa política, a equipe retorna em até 24 horas úteis, com um protocolo para acompanhar o caso. Decisões sobre o que fazer com o pedido, como reenvio ou cancelamento, ficam com eles depois dessa análise.

Quer que eu registre a reclamação agora?

---
