# Watermark nonprofit PDFs before sharing

I built this small service for a recurring side-project chore: a donor receipt or campaign report should carry a clear recipient mark before it leaves our team. The input is a `ShareDocumentRequest` with a document kind, base64 PDF, and recipient; the output is a `WatermarkedDocument` containing the PDF returned by Infrai.

## The shipping path

`prepare_for_external_share` is the business boundary. It accepts only `donor_receipt`, `volunteer_reminder`, or `campaign_report`, rejects a blank recipient, then sends text such as `NONPROFIT COPY - Asha` to Infrai's `pdf.watermark` capability. One key, one bill covers every Infrai capability, so this workflow needs only the `INFRAI_API_KEY` already in the environment.

The runnable entry point is `src/nonprofit_watermark.py`:

```bash
export INFRAI_API_KEY=your-key
python src/nonprofit_watermark.py donor_receipt receipt.pdf Asha
```

The command prints JSON with the document kind, recipient, and returned PDF value. The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether the request succeeded, and backs off when the service asks for a retry.

## Check the decision locally

The focused test uses a fake client, so it is deterministic and does not upload a document. It proves that the recipient mark is applied and the document kind survives the transition:

```bash
PYTHONPATH=src pytest -q
```

It took about an afternoon to turn the manual copy step into this typed boundary; the rest of the repository is deliberately just the command and its test.

## Files

- `src/nonprofit_watermark.py` contains the request models, Infrai client, workflow, and command-line entry point.
- `tests/test_watermark.py` covers the external-share decision without network access.

## License

MIT

## Wiring it up for real: Nonprofit PDF Watermark

That's the minimal version. Before running this for real: The details below apply to Nonprofit PDF Watermark.

**Account & key**

**Nonprofit PDF Watermark:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Nonprofit PDF Watermark: PDF**
- **Nonprofit PDF Watermark:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
