"""Tool registry: JSON schemas shown to the LLM + safe dispatch to the Python implementations.

Identity never travels through tool arguments: tools read it from the server-side Session in the
ToolContext, so a prompt-injected "I am customer 3" cannot widen access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .catalog import get_product_details, search_products
from .config import Settings
from .data import StoreData
from .handoff import HANDOFF_REASONS, escalate_to_human
from .orders import get_order_status, list_my_orders
from .policies import PolicyIndex, search_store_policies
from .session import Session


@dataclass
class ToolContext:
    data: StoreData
    policies: PolicyIndex
    session: Session
    settings: Settings
    tickets_path: Path


def build_tool_schemas(data: StoreData) -> list[dict]:
    def fn(name: str, description: str, properties: dict, required: list[str] | None = None) -> dict:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {"type": "object", "properties": properties, "required": required or []},
            },
        }

    return [
        fn(
            "search_products",
            "Busca produtos no catálogo: preço, promoção ativa, preço final, disponibilidade e estoque. "
            "Use para QUALQUER pergunta sobre produtos, preços, marcas, modelos ou faixas de preço. "
            "Exemplos: 'violões até R$ 1000' -> category='Violões', max_price=1000; "
            "'quanto custa o Takamine GD20?' -> query='Takamine GD20'.",
            {
                "query": {"type": "string", "description": "Nome, marca, modelo ou característica (ex.: 'Yamaha', 'nylon elétrico'). Não coloque preço aqui."},
                "category": {"type": "string", "enum": data.category_names},
                "min_price": {"type": "number", "description": "Preço final mínimo em reais."},
                "max_price": {"type": "number", "description": "Preço final máximo em reais (já considera promoções)."},
                "include_unavailable": {"type": "boolean", "description": "Incluir esgotados/descontinuados. Padrão: só quando há query."},
                "limit": {"type": "integer", "description": "Máximo de resultados (padrão 15)."},
            },
        ),
        fn(
            "get_product_details",
            "Detalhes de um produto (especificações, descrição, promoção, disponibilidade). Se o produto "
            "estiver indisponível, já traz alternativas disponíveis parecidas. Use depois de search_products.",
            {"product_id": {"type": "integer"}},
            ["product_id"],
        ),
        fn(
            "get_order_status",
            "Consulta um pedido: status, itens, valor, pagamento, rastreio, previsão de entrega e prazos "
            "já calculados em dias. Exige o número do pedido e o e-mail OU telefone usado na compra, "
            "exatamente como o cliente informou (não precisa se o cliente já foi identificado nesta conversa). "
            "Nunca invente ou deduza o contato.",
            {
                "order_id": {"type": "integer"},
                "contact": {"type": "string", "description": "E-mail ou telefone informado pelo cliente."},
            },
            ["order_id"],
        ),
        fn(
            "list_my_orders",
            "Lista os pedidos do cliente já identificado nesta conversa (pelo número do WhatsApp ou por uma "
            "verificação anterior). Útil quando o cliente fala em 'minha compra' sem dar o número do pedido.",
            {},
        ),
        fn(
            "search_store_policies",
            "Busca no manual de políticas da loja. Use sempre que a resposta depender de regra ou informação "
            "institucional: horário de funcionamento, endereço, telefone/WhatsApp/e-mail, formas de pagamento, "
            "parcelamento, desconto no PIX, trocas e devoluções, arrependimento, frete e prazos de entrega, "
            "rastreamento, regras de promoções, garantia, privacidade de dados.",
            {
                "query": {"type": "string", "description": "Pergunta em linguagem natural, ex.: 'prazo para devolução por arrependimento'."},
                "k": {"type": "integer", "description": "Quantidade de trechos (padrão 3, máximo 5)."},
            },
            ["query"],
        ),
        fn(
            "escalate_to_human",
            "Registra a solicitação para a equipe humana e gera um protocolo. Use para reclamações, entregas "
            "atrasadas, pedidos de devolução, troca ou cancelamento (você não executa essas operações), "
            "problemas com produto, ou quando não conseguir resolver. Informe o protocolo e o prazo ao cliente.",
            {
                "reason": {"type": "string", "enum": HANDOFF_REASONS},
                "summary": {"type": "string", "description": "Resumo objetivo do caso para o atendente."},
                "order_id": {"type": "integer", "description": "Número do pedido, se houver."},
            },
            ["reason", "summary"],
        ),
    ]


def _int(value, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{field}' deve ser um número inteiro") from None


def execute_tool(name: str, raw_arguments: str | None, ctx: ToolContext) -> dict:
    """Run a tool and always return a JSON-serializable dict (errors included) for the LLM."""
    try:
        args = json.loads(raw_arguments) if raw_arguments else {}
        if not isinstance(args, dict):
            raise ValueError("argumentos devem ser um objeto JSON")
    except (json.JSONDecodeError, ValueError) as exc:
        return {"erro": f"Argumentos inválidos para {name}: {exc}"}

    today = ctx.settings.today()
    try:
        if name == "search_products":
            allowed = {"query", "category", "min_price", "max_price", "include_unavailable", "limit"}
            return search_products(ctx.data, **{k: v for k, v in args.items() if k in allowed})
        if name == "get_product_details":
            return get_product_details(ctx.data, _int(args.get("product_id"), "product_id"))
        if name == "get_order_status":
            return get_order_status(
                ctx.data, ctx.session, today, _int(args.get("order_id"), "order_id"), args.get("contact")
            )
        if name == "list_my_orders":
            return list_my_orders(ctx.data, ctx.session, today)
        if name == "search_store_policies":
            return search_store_policies(ctx.policies, str(args.get("query", "")), args.get("k", 3))
        if name == "escalate_to_human":
            order_id = args.get("order_id")
            return escalate_to_human(
                ctx.session,
                ctx.settings.now(),
                ctx.tickets_path,
                str(args.get("reason", "outro")),
                str(args.get("summary", "")),
                _int(order_id, "order_id") if order_id not in (None, "") else None,
            )
        return {"erro": f"Ferramenta desconhecida: {name}"}
    except ValueError as exc:
        return {"erro": str(exc)}
    except Exception as exc:  # never crash the conversation because of a tool
        return {"erro": f"Falha interna ao executar {name}: {type(exc).__name__}"}
