# No pointer ID in headers
# Pointer in URL and body mismatch
# Invalid document reference - same as createDocumentReference
# Invalid document reference - changing immutable fields
# Provider ID mismatch
# No existing document reference
Feature: Producer - updateDocumentReference - Failure Scenarios

  Scenario: Invalid status
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    And a DocumentReference resource exists with values:
      | property    | value                          |
      | id          | X26-1114567890-updateDocTest   |
      | subject     | 9999999999                     |
      | status      | current                        |
      | type        | 736253002                      |
      | category    | 734163000                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | X26                            |
      | author      | X26                            |
    When producer 'X26' updates a DocumentReference 'X26-1114567890-updateDocTest' with values:
      | property | value   |
      | status   | invalid |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
        "coding": [
        {
        "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
        "code": "MESSAGE_NOT_WELL_FORMED",
        "display": "Message not well formed"
        }
        ]
        },
        "diagnostics": "Request body could not be parsed (status: String should match pattern '^current$')",
        "expression": [
        "status"
        ]
      }
      """

  Scenario: Missing content
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | TSTCUS-1114567890-updateDocTest |
      | subject     | 9999999999                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | TSTCUS                          |
      | author      | TSTCUS                          |
    When producer 'TSTCUS' requests update of a DocumentReference with pointerId 'TSTCUS-1114567890-updateDocTest' and only changing:
      """
      {
        "content": []
      }
      """
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                "code": "MESSAGE_NOT_WELL_FORMED",
                "display": "Message not well formed"
            }
            ]
        },
        "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: content)",
        "expression": [
            "DocumentReference"
        ]
      }
      """

  Scenario: contentType empty string
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | TSTCUS-1114567891-updateDocTest |
      | subject     | 9999999999                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | TSTCUS                          |
      | author      | TSTCUS                          |
    When producer 'TSTCUS' requests update of a DocumentReference with pointerId 'TSTCUS-1114567891-updateDocTest' and only changing:
      """
      {
        "content": [
          {
            "attachment": {
                "contentType": "",
                "url": "https://spine-proxy.national.ncrs.nhs.uk/https%3A%2F%2Fp1.nhs.uk%2FMentalhealthCrisisPlanReport.pdf"
            },
            "format": {
                "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
                "code": "urn:nhs-ic:unstructured",
                "display": "Unstructured Document"
            },
            "extension": [
              {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
                "valueCodeableConcept": {
                  "coding": [
                    {
                      "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                      "code": "static",
                      "display": "Static"
                    }
                  ]
                }
              }
            ]
          }
        ]
      }
      """
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                "code": "MESSAGE_NOT_WELL_FORMED",
                "display": "Message not well formed"
            }
            ]
        },
        "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: content[0].attachment.contentType)",
        "expression": [
          "DocumentReference"
        ]
      }
      """

  Scenario: Invalid contentType
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | TSTCUS-1114567892-updateDocTest |
      | subject     | 9999999999                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | TSTCUS                          |
      | author      | TSTCUS                          |
    When producer 'TSTCUS' requests update of a DocumentReference with pointerId 'TSTCUS-1114567892-updateDocTest' and only changing:
      """
      {
        "content": [
          {
            "attachment": {
                "contentType": "application/invalid",
                "url": "https://spine-proxy.national.ncrs.nhs.uk/https%3A%2F%2Fp1.nhs.uk%2FMentalhealthCrisisPlanReport.pdf"
            },
            "format": {
                "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
                "code": "urn:nhs-ic:unstructured",
                "display": "Unstructured Document"
            },
            "extension": [
              {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
                "valueCodeableConcept": {
                  "coding": [
                    {
                      "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                      "code": "static",
                      "display": "Static"
                    }
                  ]
                }
              }
            ]
          }
        ]
      }
      """
    Then the response status code is 422
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                "code": "UNPROCESSABLE_ENTITY",
                "display": "Unprocessable Entity"
            }
            ]
        },
        "diagnostics": "Invalid contentType: application/invalid. Must be 'application/pdf', 'text/html' or 'application/fhir+json'",
        "expression": [
            "content[0].attachment.contentType"
        ]
      }
      """

  Scenario: Mismatched format code and display
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | TSTCUS-1114567893-updateDocTest |
      | subject     | 9999999999                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | TSTCUS                          |
      | author      | TSTCUS                          |
    When producer 'TSTCUS' requests update of a DocumentReference with pointerId 'TSTCUS-1114567893-updateDocTest' and only changing:
      """
      {
        "content": [
          {
            "attachment": {
                "contentType": "text/html",
                "url": "https://example.org/my-doc.pdf"
            },
            "format": {
                "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
                "code": "urn:nhs-ic:record-contact",
                "display": "Unstructured Document"
            },
            "extension": [
              {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-ContentStability",
                "valueCodeableConcept": {
                  "coding": [
                    {
                      "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLContentStability",
                      "code": "static",
                      "display": "Static"
                    }
                  ]
                }
              }
            ]
          }
        ]
      }
      """
    Then the response status code is 422
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "business-rule",
        "details": {
            "coding": [
            {
                "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
                "code": "UNPROCESSABLE_ENTITY",
                "display": "Unprocessable Entity"
            }
            ]
        },
        "diagnostics": "Invalid display for format code 'urn:nhs-ic:record-contact'. Expected 'Contact details (HTTP Unsecured)'",
        "expression": [
            "content[0].format.display"
        ]
      }
      """
