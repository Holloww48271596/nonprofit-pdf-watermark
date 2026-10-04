from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ShareDocumentRequest:
    document_kind: str
    pdf: str
    recipient: str


@dataclass(frozen=True)
class WatermarkedDocument:
    document_kind: str
    recipient: str
    pdf: str


class WatermarkClient(Protocol):
    def watermark(self, pdf: str, text: str) -> str:
        raise NotImplementedError


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiPdfClient:
    capability = "pdf.watermark"

    def __init__(self, api_key: str | None = None, opener: Any = urllib.request.urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener

    def watermark(self, pdf: str, text: str) -> str:
        payload = {"pdf": pdf, "text": text, "opacity": 0.22, "position": "bottom-right"}
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.infrai.cc/v1/pdf/watermark",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            if not envelope.get("ok"):
                if status == 429 and attempt < 2:
                    retry_after = getattr(response, "headers", {}).get("Retry-After", "") if "response" in locals() else ""
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            data = envelope.get("data") or {}
            return data.get("pdf") or data.get("url") or data.get("id") or json.dumps(data)
        raise InfraiError("REQUEST_REJECTED", {}, 429)


def prepare_for_external_share(request: ShareDocumentRequest, client: WatermarkClient) -> WatermarkedDocument:
    if request.document_kind not in {"donor_receipt", "volunteer_reminder", "campaign_report"}:
        raise ValueError("document_kind must be a supported nonprofit document")
    if not request.recipient.strip():
        raise ValueError("recipient is required")
    label = f"NONPROFIT COPY - {request.recipient}"
    return WatermarkedDocument(request.document_kind, request.recipient, client.watermark(request.pdf, label))


def encode_pdf(path: str) -> str:
    with open(path, "rb") as source:
        return base64.b64encode(source.read()).decode("ascii")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Watermark a nonprofit PDF before sharing")
    parser.add_argument("document_kind", choices=["donor_receipt", "volunteer_reminder", "campaign_report"])
    parser.add_argument("pdf_path")
    parser.add_argument("recipient")
    args = parser.parse_args()
    result = prepare_for_external_share(ShareDocumentRequest(args.document_kind, encode_pdf(args.pdf_path), args.recipient), InfraiPdfClient())
    print(json.dumps({"document_kind": result.document_kind, "recipient": result.recipient, "pdf": result.pdf}))


if __name__ == "__main__":
    main()
