
# `ct600`

## Introduction

A utility for managing UK Coroporation Tax submission.  

## Caveat

This probably won't do what you want, unless you are prepared to do a fair
amount of work and data validation.  It works for me, and my workflow
running a small business.

I am registered as an HMRC developer and requested credentials for live
submission.  To use this code you need to go through the same process.

## Overview

This code is intended to be used with the following workflow:
- Previously, you will have created company accounts, and corporation tax
  computations filing in iXBRL format.
- The first step is to use `ct600` to create what I am calling a
  "form values" file.  This is a text file with 1 line for each CT600 box
  that you would fill in.  This process is partly automated, it takes
  as input the Computations iXBRL and fills in some basic CT600 fields.
  For my small business with no loss to record, this step produces
  a form values file which is mostly ready to use.
- The second step is to modify the form values file to match what you
  want to submit.  You need a text editor to do this.
  You definitely need to add boxes 975, 980 and 985
  (name, date, status) because these aren't filled in for you.
- The final step is to submit the accounts, computations and CT600 data
  in the forms values files.

### Input: iXBRL files

See [Company Tax Returns](https://www.gov.uk/company-tax-returns) and
[Corporation Tax online: support for software developers](https://www.gov.uk/government/collections/corporation-tax-online-support-for-software-developers)

This is based on my understand of HMRC's requirements, this is not advice you
should use in isolation.  Go and read the documentation above.

The accounts file needs to match what HMRC expect.  `ct600` does not parse
this file in any way, so it just needs to match what HMRC expect, which is
basically you submit what you would be submitted to Companies House
at annual filing.

The tax computations file needs to include computations data as well as
detailed profit and loss (DPL).

I use [`ixbrl-reporter-jsonnet`](https://github.com/cybermaggedon/ixbrl-reporter-jsonnet) to create iXBRL files from GnuCash.

### Creating a form values file

The command is of the form:

```
ct600 --computations ct.html --output-form-values > form-values.yaml
```

You can skip this step and create the form values file manually if you want,
but doing it this way provides a way to validate that the computations file
matches what is in the form values file.

The output will contain a field for every single box in the CT600 form,
most of which will be blank.  You can delete the blank lines if you want.

### Modifying the form values file

You will probably need to have access to the published CT600 form, and
guidance for completing it.  We're not actually going to be filling in the
form here, just making sure the form values file contains a value for
all the boxes you want to fill in.

See [CT600](https://www.gov.uk/government/publications/corporation-tax-company-tax-return-ct600-2015-version-3)

### Submission

You need to modify the `config.json` file in line with submission details.
This will contain your submission credentials.

The submission command is of the form:
```
ct600 \
    --config config.json \
    --accounts accts.html \
    --computations ct.html \
    --form-values form-values.yaml \
    --submit
```

The output is verbose.  You'll know if the submission was successful.

If there are errors, the output is not parsed particularly well, but there
will be clues about what the errors are.

If the submission works, you can use this repo to take the form values
file and overlay the data on a CT600 PDF file as a record of what you
submitted:

https://github.com/cybermaggedon/ct600-fill

## Status

This is a command-line utility, which has been tested with the HMRC test API,
as well as used for live submission.

## Credentials

In order to use this, you need production credentials (vendor ID, username,
password) for the Corporation Tax API.  HMRC does not permit these
credentials to be shared publicly.

Developer hub: 
https://developer.service.hmrc.gov.uk/api-documentation/docs/using-the-hub

## Installing

```
pip3 install .
```

## Testing

As well as the proper HMRC test systems, this packages includes an
extremely basic corptax emulator here.  It includes some validation
of the CT600 using HMRC supplied schemas.  Run:

```
scripts/corptax-test-service
```

To submit the test account data to the test service:

```
ct600 -c config.json -a accts.html -t ct600.html --submit
```

Output should look like this:
```
IRmark is hOgMwO+75eJbBax/OhPZy/NszxE=
Correlation ID is 1E242
Endpoint is http://localhost:8082/
Poll time is 1.0
Poll...
Poll...
Poll...
Poll...
Submitted successfully.
Delete request...
Completed.
```

The two files `accts.html` and `ct600.html` included in this repo
are sample accounts which were output from `ixbrl-reporter-jsonnet`.

## Usage

```
usage: ct600 [-h] [--config CONFIG] [--accounts ACCOUNTS]
             [--computations COMPUTATIONS] [--form-values FORM_VALUES]
             [--attachment ATTACHMENT] [--output-ct] [--output-values]
             [--output-form-values] [--submit] [--data-request]

Submittion to HMRC Corporation Tax API

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Configuration file (default: config.json)
  --accounts ACCOUNTS, -a ACCOUNTS
                        Company accounts iXBRL file
  --computations COMPUTATIONS, --comps COMPUTATIONS, -t COMPUTATIONS
                        Corporation tax computations iXBRL file
  --form-values FORM_VALUES, --ct600 FORM_VALUES, -f FORM_VALUES
                        CT600 form values YAML file
  --attachment ATTACHMENT, -m ATTACHMENT
                        Corporation tax computations iXBRL file
  --output-ct, -p       Just output CT message, no submission
  --output-values       Just output some data values (debug)
  --output-form-values  Output CT600 form values from computations
  --submit              Submit the CT message
  --data-request        Perform a data request for outstanding items
```

The configuration file is a JSON file, should look something like this:

```
{
    "company-type": 6,
    "declaration-name": "Sarah McAcre",
    "declaration-status": "Director",
    "username": "CTUser100",
    "password": "password",
    "gateway-test": "1",
    "tax-reference": "1234123412",
    "vendor-id": "1234",
    "software": "ct600",
    "software-version": "0.0.1",
    "url": "http://localhost:8081/",
    "title": "Ms",
    "first-name": "Sarah",
    "second-name": "McAcre",
    "email": "sarah@example.org",
    "phone": "447900123456"
}
```

# Licences, Compliance, etc.

## Warranty

This code comes with no warranty whatsoever.  See the [LICENSE](LICENCE) file
for details.  Further, I am not an accountant.  It is possible that this code
could be useful to you in meeting regulatory reporting requirements for your
business.  It is also possible that the software could report misleading
information which could land you in a lot of trouble if used for regulatory
purposes.  Really, you should check with a qualified accountant.

## Licence

Copyright (C) 2020, 2021, Cyberapocalypse Limited

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Support

You're welcome to come discuss on Discord

https://discord.gg/3cAvPASS6p