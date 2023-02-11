
from . irmark import compute as irmark_compute

import hashlib
import base64
from lxml import etree as ET
import datetime
import io
import copy
import sys

env_ns = "http://www.govtalk.gov.uk/CM/envelope"

e_GovTalkMessage = "{%s}GovTalkMessage" % env_ns
e_Header = "{%s}Header" % env_ns
e_MessageDetails = "{%s}MessageDetails" % env_ns
e_Class = "{%s}Class" % env_ns
e_Function = "{%s}Function" % env_ns
e_Qualifier = "{%s}Qualifier" % env_ns
e_SenderDetails = "{%s}SenderDetails" % env_ns
e_SenderID = "{%s}SenderID" % env_ns
e_Value = "{%s}Value" % env_ns
e_GovTalkDetails = "{%s}GovTalkDetails" % env_ns
e_Keys = "{%s}Keys" % env_ns
e_Key = "{%s}Key" % env_ns
e_URI = "{%s}URI" % env_ns
e_ChannelRouting = "{%s}ChannelRouting" % env_ns
e_Timestamp = "{%s}Timestamp" % env_ns
e_Channel = "{%s}Channel" % env_ns
e_Product = "{%s}Product" % env_ns
e_Version = "{%s}Version" % env_ns
e_IDAuthentication = "{%s}IDAuthentication" % env_ns
e_Authentication = "{%s}Authentication" % env_ns
e_Body = "{%s}Body" % env_ns
e_ResponseEndPoint = "{%s}ResponseEndPoint" % env_ns
e_CorrelationID = "{%s}CorrelationID" % env_ns
e_TransactionID = "{%s}TransactionID" % env_ns
e_Transformation = "{%s}Transformation" % env_ns
e_GatewayTest = "{%s}GatewayTest" % env_ns
e_RaisedBy = "{%s}RaisedBy" % env_ns
e_Text = "{%s}Text" % env_ns
e_Number = "{%s}Number" % env_ns
e_Type = "{%s}Type" % env_ns
e_Location = "{%s}Location" % env_ns
e_GovTalkErrors = "{%s}GovTalkErrors" % env_ns
e_Error = "{%s}Error" % env_ns
e_EnvelopeVersion = "{%s}EnvelopeVersion" % env_ns
e_Header = "{%s}Header" % env_ns

ct_ns = "http://www.govtalk.gov.uk/taxation/CT/5"

ct_IRenvelope = "{%s}IRenvelope" % ct_ns
ct_IRmark = "{%s}IRmark" % ct_ns
ct_IRheader = "{%s}IRheader" % ct_ns

sr_ns = "http://www.inlandrevenue.gov.uk/SuccessResponse"
sr_SuccessResponse = "{%s}SuccessResponse" % sr_ns
sr_Message = "{%s}Message" % sr_ns

class Message:
    def __init__(self):
        pass

    def toxml(self, tree):
        buf = io.StringIO()
        msg.write(buf, encoding="utf-8", xml_declaration=True)
        return buf.getvalue()

    def encode(self, root):
        return self.toxml(root)

    # XBRL date in English form cvt to ISO
    def to_date(self, d):
        d = datetime.datetime.strptime(d, "%d %B %Y").date()
        return str(d)

    def toprettyxml(self):
        msg = self.create_message()
        return ET.tostring(
            msg, xml_declaration=True, pretty_print=True, encoding="UTF-8"
        ).decode("utf-8")

    def tocanonicalxml(self, pre):
        post = io.StringIO()
        ET.canonicalize(xml_data=pre, out=post, strip_text=True)
        return post.getvalue()

class GovTalkMessage(Message):
    def __init__(self, params=None):
        if params == None:
            self.params = {}
        else:
            self.params = params

    @staticmethod
    def decode(data):

        if isinstance(data, str):
            root = ET.fromstring(data.encode("utf-8"))
        else:
            root = ET.fromstring(data)

        md = root.find("%s/%s" % (e_Header, e_MessageDetails))

        cls = md.find(e_Class).text
        qualifier = md.find(e_Qualifier).text
        function = md.find(e_Function).text

        if function == "submit" and qualifier == "request":
            m = GovTalkSubmissionRequest()
            m.decode_xml(root)
            return m

        if function == "submit" and qualifier == "acknowledgement":
            m = GovTalkSubmissionAcknowledgement()
            m.decode_xml(root)
            return m

        if function == "submit" and qualifier == "poll":
            m = GovTalkSubmissionPoll()
            m.decode_xml(root)
            return m

        if function == "submit" and qualifier == "error":
            m = GovTalkSubmissionError()
            m.decode_xml(root)
            return m

        if function == "submit" and qualifier == "response":
            m = GovTalkSubmissionResponse()
            m.decode_xml(root)
            return m

        if function == "delete" and qualifier == "request":
            m = GovTalkDeleteRequest()
            m.decode_xml(root)
            return m

        if function == "delete" and qualifier == "response":
            m = GovTalkDeleteResponse()
            m.decode_xml(root)
            return m

        raise RuntimeError("Can't decode")

    @staticmethod
    def create(cls, params):
        m = cls(params)
        return m

    def toxml(self):
        tree = self.create_message()
        return ET.tostring(
            tree, xml_declaration=True, encoding="UTF-8"
        )

    def create_message(self):

        root = ET.Element(
            e_GovTalkMessage, nsmap={None: env_ns, "ct": ct_ns}
        )

        ev = ET.SubElement(root, e_EnvelopeVersion)
        ev.text = "2.0"
        self.create_header(root)
        self.create_govtalk_details(root)
        self.create_body(root)

        irmark = self.get("irmark")

        if irmark:
            for elt in root.findall(".//" + ct_IRheader):
                for elt2 in root.findall(".//" + ct_IRmark):
                    elt2.text = irmark
                    elt2.set("Type", "generic")

        return ET.ElementTree(root)

    def create_header(self, root):
        header = ET.SubElement(root, e_Header)
        self.create_message_details(header)
        self.create_sender_details(header)

    def get(self, id, default=None):
        if id in self.params:
            return self.params[id]

        return default
         
    def ir_envelope(self):
        return self.params["ir-envelope"]

    def create_body(self, root):
        body = ET.SubElement(root, e_Body)
        body.append(self.ir_envelope())

    def verify_irmark(self):

        if "irmark" not in self.params:
            raise RuntimeError("No IRmark")

        irmark = self.get_irmark()
        
        if irmark != self.params["irmark"]:
            raise RuntimeError("IRmark is invalid")

    def add_irmark(self):
        self.params["irmark"] = self.get_irmark()

    def get_irmark(self):

        doc = self.create_message()
        root = doc.getroot()
        body = root.find(e_Body)
        bc = copy.deepcopy(body)

        # Magic happens, the xmlns is already in place?
        # bc.set("xmlns", env_ns)

        # Remove IRmark elements
        for hdr in bc.findall(".//" + ct_IRheader):
            for mark in hdr.findall(ct_IRmark):
                hdr.remove(mark)

        pre = io.BytesIO()
        ET.ElementTree(bc).write(pre, encoding="utf-8", xml_declaration=False)
        i = irmark_compute(pre.getvalue())

        return i

class GovTalkSubmissionRequest(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "submit"
        self.params["qualifier"] = "request"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text
        sender = header.find(e_SenderDetails)
        ida = sender.find(e_IDAuthentication)
        self.params["username"] = sender.find(e_SenderID)
        auth = ida.find(e_Authentication)
        self.params["password"] = auth.find(e_Value).text
        gtd = root.find(e_GovTalkDetails)
        self.params["tax-reference"] = gtd.find(e_Keys).find(e_Key).text
        self.params["vendor-id"] = gtd.find(e_ChannelRouting).find(e_Channel).find(e_URI).text
        self.params["software"] = gtd.find(e_ChannelRouting).find(e_Channel).find(e_Product).text
        self.params["software-version"] = gtd.find(e_ChannelRouting).find(e_Channel).find(e_Version).text

        try:
            self.params["timestamp"] = datetime.datetime.fromisoformat(
                gtd.find(e_ChannelRouting).find(e_Timestamp).text
            )
        except:
            pass

        body = root.find(e_Body)
        ire = body.find(ct_IRenvelope)
        self.params["ir-envelope"] = ire

        try:
            ts = root.find(e_Timestamp).text
            self.params["timestamp"] = datetime.datetime.fromisoformat(ts)
        except:
            pass

        try:
            self.params["email"] = sender.find(e_EmailAddress).text
        except: pass

        try:
            self.params["gateway-test"] = md.find(e_GatewayTest).text
        except: pass

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["audit-id"] = md.find(e_AuditID).text
        except:
            self.params["audit-id"] = ""

        for elt in root.findall(".//" + ct_IRheader):
            for elt2 in root.findall(".//" + ct_IRmark):
                self.params["irmark"] = elt2.text

    def create_govtalk_details(self, root):

        gtd = ET.SubElement(root, e_GovTalkDetails)

        keys = ET.SubElement(gtd, e_Keys)

        key = ET.SubElement(keys, e_Key, Type="UTR")
        key.text = self.get("tax-reference")

        td = ET.SubElement(gtd, "TargetDetails")
        ET.SubElement(td, "Organisation").text = "HMRC"

        cr = ET.SubElement(gtd, "ChannelRouting")
        ch = ET.SubElement(cr, "Channel")
        ET.SubElement(ch, "URI").text = self.get("vendor-id")
        ET.SubElement(ch, "Product").text = self.get("software")
        ET.SubElement(ch, "Version").text = self.get("software-version")
        try:
            timestamp = self.get("timestamp").isoformat()
            ET.SubElement(cr, "Timestamp").text = timestamp
        except:
            pass
              
    def create_sender_details(self, root):

        sd = ET.SubElement(root, "SenderDetails")

        ids = ET.SubElement(sd, "IDAuthentication")

        ET.SubElement(ids, "SenderID").text = self.get("username")

        auth = ET.SubElement(ids, "Authentication")
        ET.SubElement(auth, "Method").text = "clear"
        ET.SubElement(auth, "Role").text = "principal"
        ET.SubElement(auth, "Value").text = self.get("password")

        if self.get("email", "") != "":
            ET.SubElement(ids, "EmailAddress").text = self.get("email")

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, e_Class).text = self.get("class")
        ET.SubElement(md, e_Qualifier).text = self.get("qualifier")
        ET.SubElement(md, e_Function).text = self.get("function")
        ET.SubElement(md, "TransactionID").text = self.get("transaction-id")
        ET.SubElement(md, "CorrelationID")
        ET.SubElement(md, "Transformation").text = "XML"
        ET.SubElement(md, "GatewayTest").text = self.get("gateway-test", "0")

class GovTalkSubmissionAcknowledgement(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "submit"
        self.params["qualifier"] = "acknowledgement"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

        rep = md.find(e_ResponseEndPoint)
        self.params["poll-interval"] = rep.get("PollInterval")
        self.params["response-endpoint"] = rep.text

    def create_govtalk_details(self, root):

        gtd = ET.SubElement(root, "GovTalkDetails")
        ET.SubElement(gtd, "Keys")
              
    def create_sender_details(self, root):

        ET.SubElement(root, "SenderDetails")

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, "Class").text = self.get("class")
        ET.SubElement(md, "Qualifier").text = self.get("qualifier")
        ET.SubElement(md, "Function").text = self.get("function")
        ET.SubElement(md, "TransactionID").text = self.get("transaction-id", "")
        ET.SubElement(md, "CorrelationID").text = self.get("correlation-id", "")
        ET.SubElement(md, "Transformation").text = "XML"
        ET.SubElement(md, "GatewayTest").text = self.get("gateway-test", "0")
        ET.SubElement(
            md, "ResponseEndPoint", PollInterval=self.get("poll-interval")
        ).text = self.get("response-endpoint")

    def create_body(self, root):
        ET.SubElement(root, "Body")

class GovTalkSubmissionPoll(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "submit"
        self.params["qualifier"] = "poll"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

    def create_govtalk_details(self, root):

        gtd = ET.SubElement(root, "GovTalkDetails")
        ET.SubElement(gtd, "Keys")
              
    def create_sender_details(self, root):
        pass

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, "Class").text = self.get("class")
        ET.SubElement(md, "Qualifier").text = self.get("qualifier")
        ET.SubElement(md, "Function").text = self.get("function")
        ET.SubElement(md, "TransactionID").text = self.get("transaction-id", "")
        ET.SubElement(md, "CorrelationID").text = self.get("correlation-id", "")
        ET.SubElement(md, "Transformation").text = "XML"
        ET.SubElement(md, "GatewayTest").text = self.get("gateway-test", "0")

    def create_body(self, root):
        pass

class GovTalkSubmissionError(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "submit"
        self.params["qualifier"] = "error"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

        rep = md.find(e_ResponseEndPoint)
        self.params["poll-interval"] = rep.get("PollInterval")
        self.params["response-endpoint"] = rep.text

        gtd = root.find(e_GovTalkDetails)
        gte = gtd.find(e_GovTalkErrors)

        # Only use first error.
        e = gte.find(e_Error + "[1]")
        self.params["error-number"] = e.find(e_Number).text
        self.params["error-type"] = e.find(e_Type).text
        self.params["error-text"] = e.find(e_Text).text
        try:
            self.params["error-location"] = e.find(e_Location).text
        except:
            pass

    def create_govtalk_details(self, root):

        gtd = ET.SubElement(root, "GovTalkDetails")

        keys = ET.SubElement(root, "Keys")

        gte = ET.SubElement(gtd, "GovTalkErrors")

        err = ET.SubElement(gte, "Error")

        ET.SubElement(err, e_RaisedBy).text = "Gateway"
        ET.SubElement(err, e_Number).text = self.get("error-number")
        ET.SubElement(err, e_Type).text = self.get("error-type")
        ET.SubElement(err, e_Text).text = self.get("error-text")
        ET.SubElement(err, e_Location)
              
    def create_sender_details(self, root):
        pass

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, e_Class).text = self.get("class")
        ET.SubElement(md, e_Qualifier).text = self.get("qualifier")
        ET.SubElement(md, e_Function).text = self.get("function")
        ET.SubElement(md, e_TransactionID).text = self.get("transaction-id", "")
        ET.SubElement(md, e_CorrelationID).text = self.get("correlation-id", "")
        ET.SubElement(md, e_Transformation).text = "XML"
        ET.SubElement(md, e_GatewayTest).text = self.get("gateway-test", "0")
        ET.SubElement(
            md, e_ResponseEndPoint, PollInterval=self.get("poll-interval")
        ).text = self.get("response-endpoint")

    def create_body(self, root):
        pass

class GovTalkSubmissionResponse(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "submit"
        self.params["qualifier"] = "response"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

        rep = md.find(e_ResponseEndPoint)
        self.params["poll-interval"] = rep.get("PollInterval")
        self.params["response-endpoint"] = rep.text

        body = root.find(e_Body)
        sr = body.find(".//" + sr_SuccessResponse)
        self.params["success-response"] = sr

    def create_govtalk_details(self, root):
        gtd = ET.SubElement(root, "GovTalkDetails")
        ET.SubElement(gtd, "Keys")
              
    def create_sender_details(self, root):
        ET.SubElement(root, "SenderDetails")

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, e_Class).text = self.get("class")
        ET.SubElement(md, e_Qualifier).text = self.get("qualifier")
        ET.SubElement(md, e_Function).text = self.get("function")
        ET.SubElement(md, e_TransactionID).text = self.get("transaction-id", "")
        ET.SubElement(md, e_CorrelationID).text = self.get("correlation-id", "")
        ET.SubElement(md, e_Transformation).text = "XML"
        ET.SubElement(md, e_GatewayTest).text = self.get("gateway-test", "0")
        ET.SubElement(
            md, e_ResponseEndPoint, PollInterval=self.get("poll-interval")
        ).text = self.get("response-endpoint")

    def create_body(self, root):
        body = ET.SubElement(root, "Body")
        body.append(self.params["success-response"])

class GovTalkDeleteRequest(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "delete"
        self.params["qualifier"] = "request"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

    def create_govtalk_details(self, root):
        gtd = ET.SubElement(root, "GovTalkDetails")
        ET.SubElement(gtd, "Keys")
              
    def create_sender_details(self, root):
        pass

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, "Class").text = self.get("class")
        ET.SubElement(md, "Qualifier").text = self.get("qualifier")
        ET.SubElement(md, "Function").text = self.get("function")
        ET.SubElement(md, "TransactionID").text = self.get("transaction-id", "")
        ET.SubElement(md, "CorrelationID").text = self.get("correlation-id", "")
        ET.SubElement(md, "Transformation").text = "XML"
        ET.SubElement(md, "GatewayTest").text = self.get("gateway-test", "0")

    def create_body(self, root):
        pass

class GovTalkDeleteResponse(GovTalkMessage):
    def __init__(self, params=None):
        super().__init__(params)
        self.params["function"] = "delete"
        self.params["qualifier"] = "response"

    def decode_xml(self, root):
        header = root.find(e_Header)
        md = header.find(e_MessageDetails)
        self.params["class"] = md.find(e_Class).text
        self.params["function"] = md.find(e_Function).text
        self.params["qualifier"] = md.find(e_Qualifier).text

        try:
            self.params["transaction-id"] = md.find(e_TransactionID).text
        except:
            self.params["transaction-id"] = ""

        try:
            self.params["correlation-id"] = md.find(e_CorrelationID).text
        except:
            self.params["correlation-id"] = ""

        rep = md.find(e_ResponseEndPoint)
        self.params["poll-interval"] = rep.get("PollInterval")
        self.params["response-endpoint"] = rep.text

    def create_govtalk_details(self, root):
        gtd = ET.SubElement(root, "GovTalkDetails")
        ET.SubElement(gtd, "Keys")
              
    def create_sender_details(self, root):
        ET.SubElement(root, "SenderDetails")

    def create_message_details(self, root):

        md = ET.SubElement(root, e_MessageDetails)

        ET.SubElement(md, e_Class).text = self.get("class")
        ET.SubElement(md, e_Qualifier).text = self.get("qualifier")
        ET.SubElement(md, e_Function).text = self.get("function")
        ET.SubElement(md, e_TransactionID).text = self.get("transaction-id", "")
        ET.SubElement(md, e_CorrelationID).text = self.get("correlation-id", "")
        ET.SubElement(md, e_Transformation).text = "XML"
        ET.SubElement(md, e_GatewayTest).text = self.get("gateway-test", "0")
        elt = ET.SubElement(
            md, e_ResponseEndPoint,
            attrib={"PollInterval": self.get("poll-interval")}
        ).text = self.get("response-endpoint")

    def create_body(self, root):
        ET.SubElement(root, "Body")

