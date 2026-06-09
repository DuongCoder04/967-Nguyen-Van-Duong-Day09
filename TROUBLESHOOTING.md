# Troubleshooting

## Service Already Running

`start_all.sh` checks every endpoint before launch. If it reports that a
service is already running, use the existing instance or stop it from the
terminal that launched it. The script does not terminate unrelated processes.

Check the current registry:

```bash
curl http://localhost:10000/health
curl http://localhost:10000/agents
```

## Agent Is Missing from Registry

The healthy system registers four agents: customer, law, tax, and compliance.
Restart the missing agent after the registry is available. Check that
`REGISTRY_URL` points to `http://localhost:10000`.

## OpenRouter Authentication Error

Use:

```dotenv
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_real_key
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```

Confirm that the selected model is available to the account. Free models may
be rate-limited or temporarily unavailable.

## Ollama Connection or Model Error

Use:

```dotenv
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

Then verify Ollama separately:

```bash
ollama list
ollama run llama3.1:8b "Reply with OK"
```

Local inference can make the full multi-agent request take several minutes.
On the current development setup, one Ollama E2E run took about 230 seconds.

## Request Times Out

Increase the timeout when using a slow local model:

```dotenv
A2A_TIMEOUT_SECONDS=600
```

The timeout applies to delegation, the test client, dashboard queries, and the
benchmark. A timeout increase does not fix an unavailable model or dead agent.

## Empty or Very Short Response

Run the offline tests first:

```bash
uv run python -m unittest discover -s tests -v
```

Then send a traced request:

```bash
uv run python test_client.py --question "What are the consequences of tax evasion?"
```

Use the printed trace ID to find matching logs in Customer, Law, Tax, and
Compliance Agent output.

## A2AClient Deprecation Warning

The installed A2A SDK still supports the legacy `A2AClient`, so the warning
does not block this codelab. Migration to `ClientFactory` should be handled as
a dedicated SDK upgrade because it changes client construction and transport
configuration.

## Dashboard Steps and Timing

The dashboard visualizes the expected request flow. Individual step durations
are illustrative; `real_elapsed` is the actual end-to-end duration.

## Clean Verification

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q common registry customer_agent law_agent tax_agent compliance_agent stages exercises dashboard tests
bash -n start_all.sh
```
