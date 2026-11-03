# 3. Status do pedido com verificação de identidade (não trivial)

Cliente anônimo: o agente exige número do pedido + contato antes de consultar (a checagem é feita pela ferramenta, não pelo prompt), detecta o atraso calculado em código e registra um chamado com protocolo para a equipe.

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** chat anônimo  
> **Custo total:** US$ 0.0035 · As linhas 🔧 mostram as ferramentas que o agente chamou (não aparecem para o cliente).

---

**👤 Cliente:** Oi, meu pedido ainda não chegou. É o número 8.

**🎸 Duda:**

Oi! Sinto muito pela demora. Para eu consultar o pedido 8, me envia também o e-mail ou o telefone usado na compra? Assim consigo verificar o status e a previsão de entrega.

---

**👤 Cliente:** anacarol.ferreira@coldmail.com

> 🔧 `get_order_status(order_id=8, contact='anacarol.ferreira@coldmail.com')`

**🎸 Duda:**

Achei o pedido 8. Ele está **enviado e em transporte**, mas a previsão de entrega era **28/02/2026**, e já passaram **248 dias** desse prazo. Ou seja, está bem atrasado.

- Produto: Kala KA-C Concert Mogno (1 unidade)
- Valor: R$ 349,90
- Código de rastreio: BRJL5544332BR

Quer que eu registre o caso para a equipe avaliar o atraso e te dar um retorno? Se quiser, me confirma e eu abro o protocolo.

---

**👤 Cliente:** Nossa, tá muito atrasado! O que vocês podem fazer?

> 🔧 `search_store_policies(query='atraso na entrega do pedido, prazo de entrega não cumprido, o que fazer', k=5)` → `search_store_policies(query='prazo para devolução por arrependimento, troca por defeito, garantia legal e garantia do fabricante', k=5)`

**🎸 Duda:**

Entendo, Ana, esperar tanto é frustrante. Pelo que encontrei nas nossas regras:

- **Devolução por arrependimento:** é de até 7 dias após o recebimento. Como o pedido ainda não chegou, esse prazo ainda não começou.
- **Garantia legal (90 dias):** também conta a partir do recebimento, então ainda não se aplica.
- **Troca por defeito:** vale por 30 dias após a compra, e esse prazo já passou. Depois disso, a garantia é com o fabricante, e a loja pode intermediar esse processo se você pedir.

Sobre o atraso em si, as políticas que consultei não descrevem uma solução específica. Quem decide os próximos passos é a equipe. Posso registrar o caso agora com o número do pedido e o código de rastreio, e a equipe retorna em até 24 horas úteis. Quer que eu abra o protocolo?

---
