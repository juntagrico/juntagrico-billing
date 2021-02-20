import datetime
from xml.etree import ElementTree as et
from juntagrico_billing.util.payment_processor import PaymentInfo


class Camt045Reader(object):
    ns = 'urn:iso:std:iso:20022:tech:xsd:camt.054.001.04'

    def __init__(self):
        self.nsdict = {'ns': self.ns}

    def find(self, element, path):
        if element is None:
            raise PaymentReaderError("element is null")

        result = element.find(path, self.nsdict)
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
        doc = et.fromstring(xml)

        transaction = self.find(
            doc, "./ns:BkToCstmrDbtCdtNtfctn/ns:Ntfctn/ns:Ntry")

        # get valuta date
        vdate_elem = self.find(transaction, "ns:ValDt/ns:Dt")
        valuta_date = datetime.date.fromisoformat(vdate_elem.text)

        # get creditor IBAN, may be in general NtryRef element
        # sometimes its in the entry detail (see below)
        try:
            global_credit_iban = self.find(transaction, "ns:NtryRef").text
        except PaymentReaderError:
            global_credit_iban = None

        results = []

        details = self.findall(transaction, 'ns:NtryDtls/ns:TxDtls')
        for detail in details:
            amt = self.find(detail, 'ns:Amt')
            amount = float(amt.text)

            # if there is no global creditor iban, try to find it in the detail
            if global_credit_iban:
                credit_iban = global_credit_iban
            else:
                credit_iban = self.find(
                    detail, 'ns:RltdPties/ns:CdtrAcct/ns:Id/ns:IBAN').text

            refinf = self.find(detail, 'ns:RmtInf/ns:Strd/ns:CdtrRefInf')
            reftype = self.find(refinf, 'ns:Tp/ns:CdOrPrtry/ns:Prtry')

            ref = self.find(refinf, 'ns:Ref')

            id = self.find(detail, 'ns:Refs/ns:InstrId')
            results.append(
                PaymentInfo(
                    valuta_date, credit_iban,
                    amount, reftype.text, ref.text, id.text))

        return results


class PaymentReaderError(Exception):
    pass
