
import datetime

def get_values(doc):
    
    values = {}
    ns = {
        "ix": "http://www.xbrl.org/2013/inlineXBRL",
        "xbrli": "http://www.xbrl.org/2003/instance"
    }
    for elt in doc.findall(".//ix:nonNumeric", ns):
        if elt.text:
            values[elt.get("name")] = elt.text
    for elt in doc.findall(".//ix:nonFraction", ns):
        if elt.text:
            values[elt.get("name")] = elt.text

    elt = doc.find(".//xbrli:entity/xbrli:identifier[1]", ns)
    values["uk-core:UKCompaniesHouseRegisteredNumber"] = elt.text

    return values

def to_date(d):
    d = datetime.datetime.strptime(d, "%d %B %Y").date()
    return str(d)

def to_money(v):
    num = str(v).replace(",", "")
    return "%.2f" % float(num)

def to_whole_money(v):
    num = str(v).replace(",", "")
    return "%.2f" % round(float(num))
