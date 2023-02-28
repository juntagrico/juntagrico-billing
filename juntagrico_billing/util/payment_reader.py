import datetime
from xml.etree import ElementTree as et
from juntagrico_billing.util.payment_processor import PaymentInfo


class Camt045Reader(object):
    ns = 'urn:iso:std:iso:20022:tech:xsd:camt.054.001.04'

    def __init__(self):
        self.nsdict = {'ns': self.ns}

    def find_optional(self, element, path):
        if element is None:
            raise PaymentReaderError("element is null")

        # may be None, if not found
        return element.find(path, self.nsdict)

    def find(self, element, path):
        result = self.find_optional(element, path)
        if result is None:
            raise PaymentReaderError(
                "element %s not found" % path.replace('ns:', ''))

        return result

    def findall(self, element, path):
        if element is None:
            raise PaymentReaderError("element is null")

        result = element.findall(path, self.nsdict)
        if not result:
            raise PaymentReaderError(
                "elements %s not found" % path.replace('ns:', ''))

        return result

    def parse_payments(self, xml):
        results = []

        doc = et.fromstring(xml)
        root = self.find(doc, "./ns:BkToCstmrDbtCdtNtfctn/ns:Ntfctn")

        entries = self.findall(root, "ns:Ntry")
        for entry in entries:
            # get valuta date
            vdate_elem = self.find(entry, "ns:ValDt/ns:Dt")
            valuta_date = datetime.date.fromisoformat(vdate_elem.text)

            entry_ref = self.find_optional(entry, "ns:NtryRef")
            if entry_ref is not None:
                entry_iban = entry_ref.text[:21]
            else:
                entry_iban = None

            details = self.findall(entry, 'ns:NtryDtls/ns:TxDtls')
            for detail in details:
                amt = self.find(detail, 'ns:Amt')
                amount = float(amt.text)

                # if there is no global creditor iban, try to find it in the detail
                if entry_iban:
                    credit_iban = entry_iban
                else:
                    credit_iban = self.find(
                        detail, 'ns:RltdPties/ns:CdtrAcct/ns:Id/ns:IBAN').text

                refinf = self.find(detail, 'ns:RmtInf/ns:Strd/ns:CdtrRefInf')
                reftype = self.find(refinf, 'ns:Tp/ns:CdOrPrtry/ns:Prtry')

                ref = self.find(refinf, 'ns:Ref')

                # we use Refs/TxId as unique id
                id = self.find_optional(detail, 'ns:Refs/ns:InstrId')
                if id is None:
                    id = self.find_optional(detail, 'ns:Refs/ns:TxId')
                if id is None:
                    raise PaymentReaderError("couldn't find a unique id for payment. No TxId nor InstrId was found.")

                results.append(
                    PaymentInfo(
                        valuta_date, credit_iban,
                        amount, reftype.text, ref.text, id.text))

        return results


class PaymentReaderError(Exception):
    pass
