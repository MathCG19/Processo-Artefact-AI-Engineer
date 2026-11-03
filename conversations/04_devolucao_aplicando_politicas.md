# 4. Devolução — aplicando a política aos dados do pedido (não trivial)

Cliente identificado pelo número do WhatsApp (simulado). O agente cruza as datas do pedido com as regras de arrependimento (4.1), troca por defeito (4.2) e garantia (8.x) para explicar o que ainda é possível, e encaminha o caso.

> **Modelo:** `anthropic/claude-haiku-5.5` · **Data de referência:** 03/11/2026 · **Canal:** WhatsApp simulado (67) 99789-0123 (cliente identificado pelo canal)  
> **Custo total:** US$ 0.0064 · As linhas 🔧 mostram as ferramentas que o agente chamou (não aparecem para o cliente).

---

**👤 Cliente:** Oi!

**🎸 Duda:**

Oi, Letícia! Tudo bem? Sou a Duda, da Empório da Música. Em que posso te ajudar hoje? Pode ser sobre produtos, preços, um pedido ou alguma dúvida sobre a loja.

---

**👤 Cliente:** Me arrependi da minha compra, posso devolver?

> 🔧 `search_store_policies(query='prazo para devolução por arrependimento', k=3)` → `list_my_orders()` → `search_store_policies(query='garantia legal e garantia do fabricante', k=3)`

**🎸 Duda:**

Oi, Letícia! Vi aqui o seu pedido nº 7 (Shelby SU-21S Soprano, R$ 159,90). Infelizmente, o prazo para devolução por arrependimento já passou.

Pela política, o cliente tem até 7 dias corridos após o recebimento para devolver sem justificativa. Pelo que consta no sistema, o pedido foi entregue em 17/02/2026, há 259 dias. Como a data real de recebimento não foi registrada, usei a previsão de entrega como referência.

Mesmo assim, ainda há outras opções:

- **Garantia legal:** cobre defeitos de fabricação por 90 dias a partir do recebimento. Esse prazo também já passou.
- **Garantia do fabricante:** costuma durar de 6 meses a 2 anos, conforme o certificado que acompanha o produto. Se o instrumento tiver algum defeito, vale verificar esse certificado. A loja também pode intermediar esse processo se você pedir.

Posso registrar o seu caso para a equipe avaliar, inclusive se houver algum problema com o instrumento. Quer que eu faça isso?

---

**👤 Cliente:** Na verdade o ukulele tá com um chiado estranho, acho que é defeito. Tem como resolver?

> 🔧 `search_products(query='Shelby SU-21S', include_unavailable=True)`

**🎸 Duda:**

Entendi, Letícia. Infelizmente, pela política, a troca por defeito de fabricação vale por 30 dias corridos após a compra, e o seu pedido foi feito em 03/02/2026, então esse prazo já passou. A garantia legal de 90 dias a partir do recebimento também já expirou.

Ainda resta a **garantia do fabricante**, que varia de 6 meses a 2 anos conforme o certificado que vem com o produto. Se o seu ukulele ainda estiver dentro desse prazo, vale conferir o certificado. A loja também pode intermediar esse processo se você pedir.

Antes de tudo, me conta um pouco mais:
- Quando o chiado começou e em que situação ele aparece?
- Houve alguma queda, batida ou exposição a umidade?

A política não cobre danos por mau uso, quedas, umidade excessiva ou modificações. Se não houver nada disso, posso registrar o caso como problema com o produto para a equipe avaliar e entrar em contato. Quer que eu faça isso?

---

**👤 Cliente:** Pode registrar, por favor.

> 🔧 `escalate_to_human(reason='problema_com_produto', order_id=7, summary='Cliente Letícia (verificada) relata chiado estranho no ukulele Shelby SU-21S Soprano Sunburst (pedido nº 7, compra em 03/02/2026, entregue, previsão/recebimento em 17/02/2026). Cliente acredita ser defeito de fabricação. Prazos de troca por defeito (30 dias) e garantia legal (90 dias) já expiraram; resta avaliar garantia do fabricante. Cliente ainda não informou se houve queda, batida ou umidade. Também mencionou desejo de devolução por arrependimento, fora do prazo de 7 dias. Solicita avaliação da equipe.')`

**🎸 Duda:**

Pronto, Letícia. Registrei o caso para a equipe avaliar o chiado no seu ukulele.

Protocolo: **EMP-20261103-08C6**
Prazo de retorno: **até 24 horas úteis**

Se você lembrar de algo sobre quando o chiado começou ou se houve alguma queda ou batida, pode responder aqui e eu anexo ao mesmo protocolo. Enquanto isso, vale procurar o certificado de garantia do fabricante, que vem com o instrumento.

Precisa de mais alguma coisa?

---
