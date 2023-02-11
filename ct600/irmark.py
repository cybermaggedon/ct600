
import lxml.etree as ET
import io
import copy
import hashlib
import base64
import sys

def compute(xml):


    root = ET.fromstring(xml)
    
    elt = ET.Element(root.tag, nsmap={
        None: "http://www.govtalk.gov.uk/CM/envelope",
        "ct": "http://www.govtalk.gov.uk/taxation/CT/5"
    })

    for se in root:
        elt.append(copy.deepcopy(se))

    output = io.BytesIO()
    ET.ElementTree(elt).write_c14n(output)

#    print(output.getvalue().decode("utf-8"))
#    raise RuntimeError("ASD")

    shasum = hashlib.sha1(output.getvalue()).digest()
    irmark = base64.b64encode(shasum).decode("utf-8")
    return irmark

