# 4. Devolução — aplicando a política aos dados do pedido (não trivial)

Cliente identificado pelo número do WhatsApp (simulado). O agente cruza as datas do pedido com as regras de arrependimento (4.1), troca por defeito (4.2) e garantia (8.x) para explicar o que ainda é possível, e encaminha o caso.

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** WhatsApp simulado (67) 99789-0123 (cliente identificado pelo canal)  
> **Custo total:** US$ 0.0055 · As linhas **Ferramentas** mostram o que o agente consultou (não aparecem para o cliente).

---

**Cliente:** Oi!

**Duda:**

Oi, Letícia! Tudo bem? Sou a Duda, assistente da Empório da Música. Em que posso ajudar hoje? Posso buscar instrumentos e preços, consultar um pedido ou tirar dúvidas sobre a loja.

---

**Cliente:** Me arrependi da minha compra, posso devolver?

> **Ferramentas:** `search_store_policies(query='prazo para devolução por arrependimento', k=3)` → `list_my_orders()` → `search_store_policies(query='garantia legal e garantia do fabricante', k=3)`

**Duda:**

Letícia, pelo seu pedido nº 7 (Shelby SU-21S Soprano Sunburst, ukulele), o prazo de arrependimento já passou.

Pela política, a devolução por arrependimento vale por 7 dias corridos após o recebimento. Como a data real de recebimento não está registrada, usei a previsão de entrega (17/02/2026), e já se passaram 259 dias. Além disso, o produto precisa estar na embalagem original, sem sinais de uso, com todos os acessórios e manuais.

Os outros caminhos também já passaram ou dependem de outra regra:
- Troca por defeito de fabricação: até 30 dias após a compra.
- Garantia legal: 90 dias contra defeitos de fabricação, a partir do recebimento.
- Garantia do fabricante: varia de 6 meses a 2 anos, conforme o certificado que vem com o produto. Se o seu ainda estiver no prazo, é com o fabricante que você resolve, e a loja pode intermediar se você pedir.

Se quiser, registro seu caso para a equipe avaliar a situação, incluindo a questão da garantia do fabricante. Quer que eu abra o registro?

---

**Cliente:** Na verdade o ukulele tá com um chiado estranho, acho que é defeito. Tem como resolver?

**Duda:**

Sinto muito pelo chiado, Letícia. Pela política, o defeito de fabricação teria que ser tratado dentro de prazos que já passaram:

- Troca por defeito: até 30 dias após a compra. Seu pedido foi feito em 03/02/2026, então esse prazo já venceu.
- Garantia legal: 90 dias a partir do recebimento. Pela previsão de entrega (17/02/2026), já se passaram 259 dias.

Ainda pode existir a garantia do fabricante, que varia de 6 meses a 2 anos conforme o certificado que acompanha o produto. Se o seu ukulele ainda estiver dentro desse prazo, o caminho é acionar o fabricante. A loja pode intermediar o processo se você pedir.

Vou registrar o caso para a equipe avaliar o defeito e te orientar sobre a garantia do fabricante e a intermediação. Posso abrir o registro agora? Se preferir, antes disso você pode conferir o certificado de garantia que veio na caixa e me dizer a data de validade.

---

**Cliente:** Pode registrar, por favor.

> **Ferramentas:** `escalate_to_human(reason='problema_com_produto', order_id=7, summary='Cliente Letícia (verificada) relata chiado estranho no ukulele Shelby SU-21S Soprano Sunburst (pedido 7, entregue, previsão/entrega 17/02/2026, pago em 3x no cartão). Cliente acredita ser defeito. Também manifestou desejo de devolução por arrependimento, já fora do prazo de 7 dias. Troca por defeito (30 dias) e garantia legal (90 dias) vencidas pela data de referência. Cliente pode ter garantia do fabricante (6 meses a 2 anos, conforme certificado). Solicita avaliação do defeito e orientação sobre garantia do fabricante e intermediação da loja.')`

**Duda:**

Pronto, Letícia. Seu caso está registrado com o protocolo EMP-20261103-036B. A equipe deve retornar em até 24 horas úteis.

No registro ficaram o chiado no ukulele, o pedido nº 7 e a questão da garantia do fabricante. Se achar útil, guarde o número do protocolo e, enquanto isso, veja se o certificado de garantia que veio com o produto ainda está dentro do prazo.

Tem mais alguma coisa em que eu possa ajudar?

---
