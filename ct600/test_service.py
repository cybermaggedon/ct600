#!/usr/bin/env python3

from ct600.govtalk import *
from ct600.ixbrl import get_values

import time
import asyncio
from aiohttp import web
import json
import copy
import base64
import xml.etree.ElementTree as ET

try:
    import xmlschema
except ImportError:
    xmlschema = None

svc_endpoint = "http://localhost:8082/"

env_ns = "http://www.govtalk.gov.uk/CM/envelope"
ct5_ns = "http://www.govtalk.gov.uk/taxation/CT/5"

print("Loading schemas...")
hints = {
    "http://www.w3.org/2000/09/xmldsig#": "xmldsig-core-schema.xsd"
}

ct_schema = None
env_schema = None

if xmlschema:
    try:
        # ct_schema = xmlschema.XMLSchema(open("schema/CT-2014-v1-96.xsd"))
        ct_schema = xmlschema.XMLSchema(open("schema/CT-2014-v1-991.xsd"))
        env_schema = xmlschema.XMLSchema("schema/envelope-v2-0-HMRC.xsd",
                                         base_url=".", locations=hints)
        print("Loaded.")
    except Exception as e:
        print(f"Warning: Could not load schemas: {e}")
else:
    print("Warning: xmlschema not available, schema validation disabled")

class Submission:
    pass

class Api:

    def __init__(self, listen):
        self.listen = listen
        self.next_corr_id = 123456
        self.submissions = {}

    async def run(self):
        await self.serve_web()

    def error_response(self, msg, num, text):

        print("Return error:", text)

        return GovTalkSubmissionError({
            "class": msg.get("class", ""),
            "correlation-id": msg.get("correlation-id", ""),
            "transaction-id": msg.get("transaction-id", ""),
            "error-number": num,
            "error-type": "fatal",
            "error-text": text,
            "response-endpoint": svc_endpoint,
            "poll-interval": "1"
        })

    def submission_poll(self, msg):

        corr_id = msg.get("correlation-id", "")

        if corr_id not in self.submissions:
            return self.error_response(
                msg, "1000", "Correlation ID not recognised"
            )

        ready_at = self.submissions[corr_id].time + 4

#        return self.error_response(msg, "1001", "Things are all broken")

        if time.time() < ready_at:
            return GovTalkSubmissionAcknowledgement({
                "class": msg.get("class", ""),
                "correlation-id": corr_id,
                "transaction-id": msg.get("transaction-id", ""),
                "response-endpoint": svc_endpoint,
                "poll-interval": "1"
            })

        print("Submission with correlation ID %s has processed successfully" %
              corr_id)

        sr = ET.Element(sr_SuccessResponse)
        msg = ET.SubElement(sr, sr_Message)
        msg.text = "Submission processed successfully"
        msg.set("code", "0000")

        return GovTalkSubmissionResponse({
            "class": msg.get("class", ""),
            "correlation-id": corr_id,
            "transaction-id": msg.get("transaction-id", ""),
            "response-endpoint": svc_endpoint,
            "poll-interval": "1",
            "success-response": sr
        })

    def delete_request(self, msg):

        corr_id = msg.get("correlation-id", "")

        if corr_id not in self.submissions:
            return self.error_response(
                msg, "1000", "Correlation ID not recognised"
            )

        del self.submissions[corr_id]

        print("Submission with correlation ID %s deleted" % corr_id)

        return GovTalkDeleteResponse({
            "class": msg.get("class", ""),
            "correlation-id": corr_id,
            "transaction-id": msg.get("transaction-id", ""),
            "response-endpoint": svc_endpoint,
            "poll-interval": "1"
        })

    def submission_request(self, msg):

        corr_id = "%X" % self.next_corr_id
        self.next_corr_id += 1

        s = Submission()
        s.time = time.time()
        self.submissions[corr_id] = s

        ire = msg.ir_envelope()

        print()
        print("Submission received:")

        for elt in ire.findall(".//ct:IRmark", {"ct": ct5_ns}):
            print("  %-20s: %s" % ("IRmark", elt.text))

        try:
            ts = msg.get("timestamp")
            if ts:
                print("  %-20s: %s" % ("Timestamp", ts))
        except:
            pass

        for elt in ire.findall(".//ct:CompanyName", {"ct": ct5_ns}):
            print("  %-20s: %s" % ("Company", elt.text))

        for elt in ire.findall(".//ct:Reference", {"ct": ct5_ns}):
            print("  %-20s: %s" % ("UTR", elt.text))

        for elt in ire.findall(".//ct:ChargeableProfits", {"ct": ct5_ns}):
            print("  %-20s: %10.2f" % ("Profit", float(elt.text)))

        for elt in ire.findall(".//ct:Turnover/ct:Total", {"ct": ct5_ns}):
            print("  %-20s: %10.2f" % ("Turnover", float(elt.text)))

        for elt in ire.findall(".//ct:TaxPayable", {"ct": ct5_ns}):
            print("  %-20s: %10.2f" % ("Tax payable", float(elt.text)))

        for elt in ire.findall(".//ct:PeriodCovered/ct:From", {"ct": ct5_ns}):
            print("  %-20s: %s" % ("Start of period", elt.text))

        for elt in ire.findall(".//ct:PeriodCovered/ct:To", {"ct": ct5_ns}):
            print("  %-20s: %s" % ("End of period", elt.text))

        try:
            # FIXME: IRmark switched off
            msg.verify_irmark()
            print("IRmark is valid.")
        except Exception as e:
            print("Exception:", e)
            print("IRmark is invalid")
#            raise RuntimeError("IRmark is invalid")

        for elt in ire.findall(".//ct:Computation//ct:EncodedInlineXBRLDocument", {"ct": ct5_ns}):
            comps = base64.b64decode(elt.text)
            open("received/comps.html", "wb").write(comps)
            print("Wrote received/comps.html")
            doc = ET.fromstring(comps)
            vals = get_values(doc)
            print("Computations document has %d facts" % len(vals))

        for elt in ire.findall(".//ct:Accounts//ct:EncodedInlineXBRLDocument", {"ct": ct5_ns}):
            accts = base64.b64decode(elt.text)
            open("received/accts.html", "wb").write(accts)
            print("Wrote received/accts.html")
            doc = ET.fromstring(accts)
            vals = get_values(doc)
            print("Accounts document has %d facts" % len(vals))

        for elt in ire.findall(".//ct:AttachedFiles//ct:Attachment", {"ct": ct5_ns}):
            att = base64.b64decode(elt.text)
            fname = elt.get("Filename")
            open("received/" + fname, "wb").write(att)
            print("Wrote received/" + fname)

        # The CT is invalid by the schema, need to remove IRmark if it exists
        ct_copy = copy.deepcopy(ire)

        open("received/ct.xml", "wb").write(
            ET.tostring(ct_copy, xml_declaration=True)
            #, default_namespace=ct5_ns)
        )
        print("Wrote received/ct.xml")

        tree = copy.deepcopy(msg.create_message())
#        for elt in tree.findall("{%s}Body" % env_ns):
#            for elt2 in elt:
#                elt.remove(elt2)

        open("received/govtalk.xml", "wb").write(
            ET.tostring(tree.getroot(), xml_declaration=True)
        )
        print("Wrote received/govtalk.xml")

        ## FIXME: ???  I think we have a namespace problem?
        ct_copy = ET.parse("received/ct.xml")
        tree = ET.parse("received/govtalk.xml")

        if ct_schema:
            try:
                ct_schema.validate(ct_copy)
                print("Corporation tax validates against schema.")
            except Exception as e:
                print("Corporation tax body is not valid.")
                print(str(e))
        else:
            print("Schema validation skipped (xmlschema not available)")

        if env_schema:
            try:
                env_schema.validate(tree.getroot())
                print("Envelope validates against schema.")
            except Exception as e:
                print("Envelope is not valid.")
                print(str(e))
        else:
            print("Envelope validation skipped (xmlschema not available)")

        resp = GovTalkSubmissionAcknowledgement({
            "class": msg.get("class", ""),
            "correlation-id": corr_id,
            "transaction-id": msg.get("transaction-id", ""),
            "response-endpoint": svc_endpoint,
            "poll-interval": "1",
        })

        print("Assigned correlation ID", corr_id)

        return resp

    async def post(self, request):

        req = await request.read()

        msg = GovTalkMessage.decode(req)

        try:

            if isinstance(msg, GovTalkSubmissionRequest):
                resp = self.submission_request(msg)
            elif isinstance(msg, GovTalkSubmissionPoll):
                resp = self.submission_poll(msg)
            elif isinstance(msg, GovTalkDeleteRequest):
                resp = self.delete_request(msg)
            else:
                raise RuntimeError("Not implemented.")

            return web.Response(
#                body=resp.toprettyxml(),
                body=resp.toxml(),
                content_type="application/xml"
            )

        except Exception as e:

            resp = self.error_response(msg, "1000", str(e))

            return web.Response(
#                body=resp.toprettyxml(),
                body=resp.toxml(),
                content_type="application/xml"
            )

    async def serve_web(self):
        
        async def post(request):

            resp = {
                'status': 'OK'
            }
            
            return web.Response(
                body=json.dumps(resp, indent=4) + "\n",
                content_type="application/json"
            )

        app = web.Application()
        app.router.add_post('/', self.post)

        runner = web.AppRunner(app)
        await runner.setup()

        for ep in self.listen:
            host = ep.split(":", 2)

            site = web.TCPSite(runner, host[0], host[1])
            await site.start()

            print("Started endpoint on", ep)

        while True:
            await asyncio.sleep(10)

def main():
    svc = Api(["localhost:8081", "localhost:8082"])

    loop = asyncio.new_event_loop()
    print("Launching service...")
    loop.run_until_complete(svc.run())

if __name__ == "__main__":
    main()