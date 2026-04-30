Feature: Producer - upsertDocumentReference - Failure Scenarios

  Scenario: Invalid category for type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' upserts a DocumentReference with values:
      | property  | value                          |
      | id        | X26-testid-upsert-0001-0001    |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 1102421000000108               |
      | custodian | X26                            |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
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
        "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
        "expression": [
        "category.coding[0].code"
        ]
      }
      """

  Scenario: Invalid status
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' upserts a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | X26                            |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
      | status    | invalid                        |
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

  Scenario: System not supported in NRL 3.0
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' upserts a DocumentReference with values:
      | property     | value                          |
      | id           | X26-testid-upsert-0001-0001    |
      | subject      | 9278693472                     |
      | status       | current                        |
      | type_system  | http://invalidsystem.info/sct  |
      | type_display | Mental health crisis plan      |
      | type         | 736253002                      |
      | category     | 734163000                      |
      | custodian    | ANGY1                          |
      | author       | HAR1                           |
      | url          | https://example.org/my-doc.pdf |
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
      "diagnostics": "Invalid type system: http://invalidsystem.info/sct Type system must be either 'http://snomed.info/sct', 'https://nicip.nhs.uk' or 'https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordType'",
      "expression": ["type.coding[0].system"]
      }
      """

  Scenario: Invalid Document Reference Type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' upserts a DocumentReference with values:
      | property     | value                          |
      | id           | X26-testid-upsert-0001-0001    |
      | subject      | 9999999999                     |
      | status       | current                        |
      | type         | invalid                        |
      | type_system  | http://snomed.info/sct         |
      | type_display | Mental health crisis plan      |
      | category     | 734163000                      |
      | custodian    | ANGY1                          |
      | author       | HAR1                           |
      | url          | https://example.org/my-doc.pdf |
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
        "diagnostics": "Invalid type code: invalid Type must be a member of the England-NRLRecordType value set (https://fhir.nhs.uk/England/CodeSystem/England-NRLRecordType)",
        "expression": [
            "type.coding[0].code"
        ]
      }
      """

  Scenario: Mismatched Category Code for Document Reference Type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' upserts a DocumentReference with values:
      | property  | value                          |
      | id        | X26-testid-upsert-0001-0001    |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 1102421000000108               |
      | custodian | X26                            |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
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
        "diagnostics": "The Category code of the provided document 'http://snomed.info/sct|1102421000000108' must match the allowed category for pointer type 'http://snomed.info/sct|736253002' with a category value of 'http://snomed.info/sct|734163000'",
        "expression": [
        "category.coding[0].code"
        ]
      }
      """

  Scenario Outline: Invalid display value for type or category (imaging)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system               | value |
      | https://nicip.nhs.uk | MAULR |
      | https://nicip.nhs.uk | MAXIB |
    When producer 'ANGY1' upserts a DocumentReference with values:
      | property     | value                          |
      | id           | ANGY1-testid-upsert-0001-0001  |
      | subject      | 9999999999                     |
      | status       | current                        |
      | type_system  | <type-system>                  |
      | type_display | <type-display>                 |
      | type         | <type-code>                    |
      | category     | <category-code>                |
      | custodian    | ANGY1                          |
      | author       | HAR1                           |
      | url          | https://example.org/my-doc.pdf |
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
        "diagnostics": "type code '<type-code>' must have a display value of '<correct-display>'",
        "expression": [
          "type.coding[0].display"
        ]
      }
      """

    Examples:
      | type-system          | type-code | category-code | type-display       | correct-display   |
      | https://nicip.nhs.uk | MAULR     | 721981007     | "Nonsense display" | MRA Upper Limb Rt |
      | https://nicip.nhs.uk | MAXIB     | 103693007     | "Nonsense display" | MRI Axilla Both   |

  Scenario: Missing content
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests upsert of a DocumentReference with pointerId 'TSTCUS-sample-id-00001' and default test values except 'content' is:
      """
      "content": []
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
    When producer 'TSTCUS' requests upsert of a DocumentReference with pointerId 'TSTCUS-sample-id-00002' and default test values except 'content' is:
      """
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
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' upserts a DocumentReference with values:
      | property    | value                          |
      | id          | TSTCUS-sample-id-00003         |
      | subject     | 9999999999                     |
      | status      | current                        |
      | type        | 736253002                      |
      | category    | 734163000                      |
      | custodian   | ANGY1                          |
      | author      | HAR1                           |
      | url         | https://example.org/my-doc.pdf |
      | contentType | application/invalid            |
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
    When producer 'TSTCUS' requests upsert of a DocumentReference with pointerId 'TSTCUS-testid-upsert-0001-0001' and default test values except 'content' is:
      """
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
