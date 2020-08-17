type_codes = {'subscription': '01', 'share': '02', 'extra': '03'}


def calculate_check_number(ref_number):
    numbers = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5]
    overfloat = 0
    for n in ref_number:
        overfloat = numbers[(overfloat + int(n)) % 10]
    return str((10 - overfloat) % 10)


def generate_ref_number(billtype, bill_id, billable_id):
    type_code = type_codes.get(billtype, '00')
    bill_code = str(bill_id).rjust(12, '0')
    billable_code = str(billable_id).rjust(12, '0')
    without_cs = type_code + billable_code + bill_code
    cs = calculate_check_number(without_cs)
    return without_cs + cs
