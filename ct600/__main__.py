#!/usr/bin/env python3

from ct600.govtalk import *
from ct600.corptax import *

import xml.etree.ElementTree as ET
import lxml.etree
import asyncio
import aiohttp
import time
import xml.dom.minidom
import sys
import argparse
import json
import datetime
import textwrap
import yaml

version = "1.0.0"

def load_comps(path):
    try:
        return open(path, "rb").read()
    except Exception as e:
        raise RuntimeError("Could not read computations file: %s" % str(e))

def load_accts(path):
    try:
        return open(path, "rb").read()
    except Exception as e:
        raise RuntimeError("Could not read accounts file: %s" % str(e))

def get_schema(file):

    doc = ET.parse(file)

    schema=set()
    for elt in doc.findall(".//ix:references/link:schemaRef", {
            "link": "http://www.xbrl.org/2003/linkbase",
            "xlink": "http://www.w3.org/1999/xlink",
            "ix": "http://www.xbrl.org/2013/inlineXBRL"
    }):
        schema.add(elt.get("{%s}href" % "http://www.w3.org/1999/xlink"))

    return schema

def check_schemas(accts, comps):

    # Sanity check on inputs, correct schemas in use?

    schema = get_schema(accts)
    found_frc=False
    found_dpl=False
    found_ct=False

    for s in schema:
        if s.startswith("https://xbrl.frc.org.uk/FRS-"):
            found_frc = True
        if s.startswith("https://xbrl.frc.org.uk/dpl/"):
            found_dpl = True

    schema = get_schema(comps)

    for s in schema:
        if s.startswith("http://www.hmrc.gov.uk/schemas/ct/comp/"):
            found_ct = True
        if s.startswith("https://xbrl.frc.org.uk/dpl/"):
            found_dpl = True

    if not found_dpl:
        sys.stderr.write("No DPL schema present in either file!\n")
        sys.stderr.write(
            "One of the files should contain DPL schema statement.\n")
        sys.exit(1)

    if not found_frc:
        sys.stderr.write("No FRS schema present in company accounts!\n")
        sys.stderr.write("Is it a company accounts file?\n")
        sys.exit(1)

    if not found_ct:
        sys.stderr.write("No CT schema present in computations file!\n")
        sys.stderr.write("Is it a corporation tax computations file?\n")
        sys.exit(1)

def request_params(params, utr, doc):

    req_params = {
        "username": params["username"],
        "password": params["password"],
        "class": "HMRC-CT-CT600",
        "gateway-test": params["gateway-test"],
        "tax-reference": utr,
        "vendor-id": params["vendor-id"],
        "software": "ct600",
        "software-version": version,
        "ir-envelope": doc
    }

    if "class" in params:
        req_params["class"] = params["class"]

    if "timestamp" in params:
        req_params["timestamp"] = datetime.datetime.fromisoformat(
            params["timestamp"]
        )

    return req_params

def get_govtalk_message(params, utr, doc):

    req_params = request_params(params, utr, doc.getroot())
    return GovTalkSubmissionRequest(req_params)

def get_bundle(args):

    if args.config is None:
        raise RuntimeError("Must specify a config")

    if args.accounts is None:
        raise RuntimeError("Must specify an accounts file")

    if args.computations is None:
        raise RuntimeError("Must specify a computations file")

    if args.form_values is None:
        raise RuntimeError("Must specify a form-values file")

    check_schemas(args.accounts, args.computations)

    accts = load_comps(args.accounts)

    corptax = load_comps(args.computations)
    comps = Computations(corptax)

    try:
        form_values = open(args.form_values, "r").read()
        form_values = yaml.safe_load(form_values)
    except Exception as e:
        raise RuntimeError("Could not read form values file: %s" % str(e))

    # Load config
    params = json.loads(open(args.config).read())

    if args.attachment is not None:
        atts = {
            filename: open(filename, "rb").read()
            for filename in args.attachment
        }
    else:
        atts = {}

    return InputBundle(corptax, accts, form_values, params, atts)

async def call(req, ep):

    async with aiohttp.ClientSession() as session:

        data = req.toxml()

        async with session.post(ep, data=data) as resp:
            if resp.status != 200:
                print(await resp.text())
                raise RuntimeError(
                    "Transaction failed: status=%d" % resp.status
                )
            data = await resp.text()

            msg = GovTalkMessage.decode(data)

            if isinstance(msg, GovTalkSubmissionError):
                print(data)
                raise RuntimeError(msg.get("error-text"))

            return msg

async def submit(req, params):

    resp = await call(req, params["url"])

    correlation_id = resp.get("correlation-id")
    endpoint = resp.get("response-endpoint")
    try:
        poll = float(resp.get("poll-interval"))
    except:
        poll = None

    print("Correlation ID is", correlation_id)

    timeout = time.time() + 120
    
    while not isinstance(resp, GovTalkSubmissionResponse):

        if time.time() > timeout:
            raise RuntimeError("Timeout waiting for valid response.")

        if poll == None:
            raise RuntimeError(
                "Should be polling, but have no poll information?"
            )

        await asyncio.sleep(poll)

        req = GovTalkSubmissionPoll({
            "username": params["username"],
            "password": params["password"],
            "class": "HMRC-CT-CT600",
            "gateway-test": params["gateway-test"],
            "correlation-id": correlation_id
        })

        print("Poll...")
        resp = await call(req, endpoint)
        correlation_id = resp.get("correlation-id")
        endpoint = resp.get("response-endpoint")
        try:
            poll = float(resp.get("poll-interval"))
        except:
            poll = None

    sr = resp.get("success-response")
    for elt in sr.findall(".//" + sr_Message):
        print("- Message " + "-" * 68)
        print(elt.text)
    print("-" * 76)

    print("Submission was successful.")

    if correlation_id == None or correlation_id == "":
        print("Completed.")
        return

    req = GovTalkDeleteRequest({
        "username": params["username"],
        "password": params["password"],
        "class": "HMRC-CT-CT600",
        "gateway-test": params["gateway-test"],
        "correlation-id": correlation_id
    })

    print("Delete request...")
    resp = await call(req, endpoint)

    print("Completed.")

def output_form_values(args):

    if args.computations is None:
        raise RuntimeError("Must specify a computations file")

    corptax = load_comps(args.computations)
    comps = Computations(corptax)

    print("ct600:")

    for c in comps.to_values():

        print()
        help = "\n  # ".join(textwrap.wrap(c.description, width=75))
        print("  # " + help)

        # Special case hack for address.
        if c.box == 960:
            print("  960:")
            print("  - Address line 1")
            print("  - Address line 2")
            continue

        if c.value is None:
            print("  " + str(c.box) + ": ")
        else:
            print("  " + str(c.box) + ": " + str(c.value))

    print()

def output_values(args):

    if args.computations is None:
        raise RuntimeError("Must specify a computations file")

    corptax = load_comps(args.computations)
    comps = Computations(corptax)

    for c in comps.to_values():

        if c.value is None: continue

        print(
            "%-4d %-45s: %s" % (
                c.box, c.description[:44], str(c.value)[:20]
            )
        )

def output_ct(args):

    bundle = get_bundle(args)

    rtn = bundle.get_return()
    utr = str(bundle.form_values["ct600"][3])

    gtm = get_govtalk_message(bundle.params, utr, rtn)

    print(gtm.toprettyxml())

def submit_ct(args):

    bundle = get_bundle(args)

    rtn = bundle.get_return()
    utr = str(bundle.form_values["ct600"][3])

    req = get_govtalk_message(bundle.params, utr, rtn)

    req.add_irmark()

    print("IRmark is", req.get_irmark())

    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(submit(req, bundle.params))
    except Exception as e:
        print("Exception:", str(e))
        raise e

# FIXME: Not known to work
def data_request(args):

    raise RuntimeError("Not implemented")

    async def doit():
        req_params = {
            "username": params["username"],
            "password": params["password"],
            "class": "HMRC-CT-CT600",
            "gateway-test": params["gateway-test"],
            "vendor-id": params["vendor-id"],
            "software": params["software"],
            "software-version": params["software-version"],
            "ir-envelope": lxml.etree.Element("asd")
        }

        if "class" in params:
            req_params["class"] = params["class"]

        if "timestamp" in params:
            req_params["timestamp"] = datetime.datetime.fromisoformat(
                params["timestamp"]
            )

        req = GovTalkSubmissionRequest(req_params)
        req.params["function"] = "list"
        req.params["qualifier"] = "request"

        print(req.toxml())
        resp = await call(req, params["url"])
        print(resp)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(doit())

def main():

    # Command-line argument parser
    parser = argparse.ArgumentParser(
        description="Submittion to HMRC Corporation Tax API"
    )
    parser.add_argument('--config', '-c',
                        default='config.json',
                        help='Configuration file (default: config.json)')
    parser.add_argument('--accounts', '-a', required=False,
                        help='Company accounts iXBRL file')
    parser.add_argument('--computations', '--comps', '-t', required=False,
                        help='Corporation tax computations iXBRL file')
    parser.add_argument('--form-values', '--ct600', '-f', required=False,
                        help='CT600 form values YAML file')
    parser.add_argument('--attachment', '-m', required=False, action='append',
                        help='Extra attachment to include with filing e.g. PDF')
    parser.add_argument('--output-ct', '-p',
                        action="store_true", default=False,
                        help='Just output CT message, no submission')
    parser.add_argument('--output-values',
                        action="store_true", default=False,
                        help='Just output some data values (debug)')
    parser.add_argument('--output-form-values',
                        action="store_true", default=False,
                        help='Output CT600 form values from computations')
    parser.add_argument('--submit',
                        action="store_true", default=False,
                        help='Submit the CT message')
    parser.add_argument('--data-request',
                        action="store_true", default=False,
                        help='Perform a data request for outstanding items')

    # Parse arguments
    args = parser.parse_args(sys.argv[1:])

    if args.output_values:
        output_values(args)
        sys.exit(0)

    if args.output_form_values:
        output_form_values(args)
        sys.exit(0)

    if args.output_ct:
        output_ct(args)
        sys.exit(0)

    if args.submit:
        submit_ct(args)
        sys.exit(0)

    if args.data_request:
        data_request(args)
        sys.exit(0)

if __name__ == "__main__":

    main()

