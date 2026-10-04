from nonprofit_watermark import ShareDocumentRequest, prepare_for_external_share


class FakeClient:
    def __init__(self):
        self.calls = []

    def watermark(self, pdf, text):
        self.calls.append((pdf, text))
        return "watermarked-pdf"


def test_external_share_adds_recipient_mark_and_preserves_kind():
    client = FakeClient()
    result = prepare_for_external_share(ShareDocumentRequest("donor_receipt", "raw-pdf", "Asha"), client)
    assert result.pdf == "watermarked-pdf"
    assert result.document_kind == "donor_receipt"
    assert client.calls == [("raw-pdf", "NONPROFIT COPY - Asha")]
