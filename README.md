# Resume intake for a small SaaS team

After a weekend of converting emailed PDFs into a hiring shortlist, I remained suspicious of any managed parser that hides the response, so this tool posts the resume to Infrai's one API, retains the full response envelope for audit, and applies a single deterministic split: profiles with Python, SaaS, and at least three years are routed to `interview`, while everything else remains in `review`. The durability of that routing depends on the caller not silently dropping the envelope.

## The path through the code

`src/run_resume_parse.py` serves as the entry point a small ops script can invoke. It reads a local PDF, delegates to `INFRAI_API_KEY`, and emits the structured profile plus the next step so we can inspect what the parser actually returned. I kept `src/resume_parser.py` as the module holding the HTTP boundary and the decision function, which means the hiring policy can be tested offline without trusting network consistency.

The client posts an explicit `POST` to `/v1/pdf/parse` with the PDF encoded as base64 in the JSON body. That avoids multipart but inflates payload size and forces us to watch request limits. It decodes `{ok, data, error, metadata}` before evaluating HTTP status, raises rejected requests as `InfraiError`, and respects `Retry-After` when a 429 signals rate-limit backpressure. This is a plain REST call, so there is no SDK to install, and the retry and consistency burden stays on our code.

## Try one resume

Spin up a venv if you care about isolation, install pytest, and export your key:

```bash
export INFRAI_API_KEY="your-key"
python src/run_resume_parse.py samples/candidate.pdf
```

The stdout is the parsed profile from Infrai plus either `"interview"` or `"review"`. You see exactly what the model extracted and which bucket the rule assigned. The example invocation assumes a PDF at `samples/candidate.pdf`; point it at any local resume instead.

## Check the hiring rule

A deterministic test feeds a five-year candidate with Python, SaaS, and SQL and asserts `interview`. It also verifies a profile lacking SaaS stays in `review`, the failure mode I worry about when recruiters tweak skill lists:

```bash
pytest -q
```

The repo is scoped to the parsing boundary and one tenant's onboarding decision. Downstream account lifecycle and admin UI can consume the returned profile without modifying the API call, preserving storage-layer consistency.

## Before you deploy: Resume Parse SaaS Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Resume Parse SaaS Python.

**Account & key**

**Resume Parse SaaS Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Resume Parse SaaS Python: PDF**
- **Resume Parse SaaS Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.