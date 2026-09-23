garak.generators.a2a
====================

Agent-to-Agent (A2A) protocol connector for multi-agent systems.

This generator enables garak to run vulnerability probes against AI agents
communicating over the Agent-to-Agent (A2A) protocol (task-based message exchange
over JSON-RPC 2.0).

It supports:

* Automatic protocol negotiation: A2A spec 0.3+ (``message/send`` with ``kind: "text"``)
  with fallback to spec 0.2 (``tasks/send`` with ``type: "text"``) upon JSON-RPC error ``-32601``.
* Multi-turn session task continuity: preserves the server-issued ``taskId`` across
  conversation turns.
* Refusal extraction: captures JSON-RPC error responses as structured evidence
  (``[A2A Refusal] ...``) for detector evaluation.
* Agent Card discovery: fetches and parses ``/.well-known/agent-card.json`` via ``get_agent_card()``.

Configuration Options
---------------------

Uses the following options from ``_config.plugins.generators["a2a"]["A2AGenerator"]``:

* ``uri`` - the A2A endpoint URL; can also be passed as the generator name / target name
* ``auth_token`` - Bearer token for HTTP Authorization header
* ``api_key`` - custom API key
* ``api_key_header`` - header name for custom API key (default: ``X-API-Key``)
* ``dialect`` - protocol dialect: ``"auto"`` (default), ``"v03"``, or ``"v02"``
* ``request_timeout`` - HTTP request timeout in seconds (default: 30)
* ``verify_ssl`` - whether to enforce SSL certificate validation (default: ``True``)

.. automodule:: garak.generators.a2a
   :members:
   :undoc-members:
   :show-inheritance:
