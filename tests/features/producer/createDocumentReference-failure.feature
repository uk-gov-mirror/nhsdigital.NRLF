# Invalid document reference - structure
# Invalid document reference - required fields missing
# Invalid document reference - extra fields provided
# Invalid document reference - missing custodian identifier
# Invalid document reference - missing subject identifier
# Invalid document reference - invalid custodian system
# Invalid document reference - invalid subject system
# Invalid document reference - invalid relatesTo code
# Invalid document reference - invalid relatesTo target
# Invalid document reference - multiple type.coding
# Invalid document reference - invalid custodian suffix
Feature: Producer - createDocumentReference - Failure Scenarios

  Scenario: Producer and custodian ODS mismatch
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | N0TANGY                        |
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
        "diagnostics": "The custodian of the provided DocumentReference does not match the expected ODS code for this organisation",
        "expression": [
            "custodian.identifier.value"
        ]
      }
      """

  Scenario: Invalid NHS number (correct length but not valid)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 1234567890                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    # NRL-765 known bug: this response is not handled properly, currently gives a 500
    # Then the response status code is 400
    Then the response is an OperationOutcome with 1 issue

  # And the OperationOutcome contains the issue:
  # """
  # {
  # "severity": "error",
  # "code": "informational",
  # "details": {
  # "coding": [
  # {
  # "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
  # "code": "BAD_REQUEST",
  # "display": "Bad request"
  # }
  # ]
  # },
  # "diagnostics": "Invalid NHS number"
  # }
  # """
  Scenario: Invalid NHS number (valid number but wrong system)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'subject' is:
      """
      "subject": {
        "identifier": {
            "system": "https://fhir.nhs.uk/Id/not-nhs-number",
            "value": "9999999999"
        }
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
        "diagnostics": "Provided subject identifier system is not the NHS number system (expected 'https://fhir.nhs.uk/Id/nhs-number')",
        "expression": [
            "subject.identifier.system"
        ]
      }
      """

  Scenario: Invalid Author
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'author' is:
      """
      "author":[{
        "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "!!!!!"
        }
      }]
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
        "diagnostics": "Invalid author value: '!!!!!' Author value must be alphanumeric",
        "expression": [
            "author[0].identifier.value"
        ]
      }
      """

  Scenario: Invalid Author System
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'author' is:
      """
      "author":[{
        "identifier": {
            "system": "ddddd",
            "value": "123"
        }
      }]
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
        "diagnostics": "Invalid author system: 'ddddd' Author system must be 'https://fhir.nhs.uk/Id/ods-organization-code'",
        "expression": [
            "author[0].identifier.system"
        ]
      }
      """

  # Invalid document reference - invalid relatesTo target
  # Invalid document reference - invalid producer ID in relatesTo target
  Scenario: Unauthorised supersede - target belongs to a different custodian
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                           |
      | id          | N0TANGY-111-UnauthSupersedeTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | N0TANGY                         |
      | author      | HAR1                            |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property   | value                           |
      | subject    | 9278693472                      |
      | status     | current                         |
      | type       | 736253002                       |
      | category   | 734163000                       |
      | custodian  | ANGY1                           |
      | author     | HAR1                            |
      | url        | https://example.org/newdoc.pdf  |
      | supercedes | N0TANGY-111-UnauthSupersedeTest |
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
        "diagnostics": "The relatesTo target identifier value does not include the expected ODS code for this organisation",
        "expression": [
            "relatesTo[0].target.identifier.value"
        ]
      }
      """
    And the Document Reference 'N0TANGY-111-UnauthSupersedeTest' exists with values:
      | property    | value                           |
      | id          | N0TANGY-111-UnauthSupersedeTest |
      | subject     | 9278693472                      |
      | status      | current                         |
      | type        | 736253002                       |
      | category    | 734163000                       |
      | contentType | application/pdf                 |
      | url         | https://example.org/my-doc.pdf  |
      | custodian   | N0TANGY                         |

  # Invalid document reference - superseded document reference not found
  # Invalid document reference - superseded document reference NHS number mismatch
  # Invalid document reference - superseded document reference pointer type mismatch
  # Credentials - no pointer types allowed
  Scenario: Producer lacks permissions to create any pointer types
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system | value |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 736253002                      |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "Your organisation 'ANGY1' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Invalid status
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' creates a DocumentReference with values:
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

  Scenario: Producer lacks the permission for the pointer type requested
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property  | value                          |
      | subject   | 9999999999                     |
      | status    | current                        |
      | type      | 887701000000100                |
      | category  | 734163000                      |
      | custodian | ANGY1                          |
      | author    | HAR1                           |
      | url       | https://example.org/my-doc.pdf |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
              "code": "AUTHOR_CREDENTIALS_ERROR",
              "display": "Author credentials error"
            }
          ]
        },
        "diagnostics": "The type of the provided DocumentReference is not in the list of allowed types for this organisation",
        "expression": [
          "type.coding[0].code"
        ]
      }
      """

  Scenario: Invalid category for type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' creates a DocumentReference with values:
      | property  | value                          |
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

  Scenario: Invalid format code for attachment type contact details
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
      """
      "content": [
        {
          "attachment": {
              "contentType": "text/html",
              "url": "someContact.co.uk"
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
        "diagnostics": "Invalid content format code: urn:nhs-ic:unstructured format code must be 'urn:nhs-ic:record-contact' for Contact details attachments.",
        "expression": [
          "content[0].format.code"
        ]
      }
      """

  Scenario: Invalid format code for attachment type pdf
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
      """
      "content": [
        {
          "attachment": {
              "contentType": "application/pdf",
              "language": "en-UK",
              "url": "https://spine-proxy.national.ncrs.nhs.uk/https%3A%2F%2Fp1.nhs.uk%2FMentalhealthCrisisPlanReport.pdf",
              "hash": "2jmj7l5rSw0yVb/vlWAYkK/YBwk=",
              "title": "Mental health crisis plan report",
              "creation": "2022-12-21T10:45:41+11:00"
          },
          "format": {
              "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
              "code": "urn:nhs-ic:record-contact",
              "display": "Contact details (HTTP Unsecured)"
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
        "diagnostics": "Invalid content format code: urn:nhs-ic:record-contact format code must be 'urn:nhs-ic:unstructured' for Unstructured Document attachments.",
        "expression": [
          "content[0].format.code"
        ]
      }
      """

  # Invalid document reference - empty content[0].attachment.url
  # Invalid document reference - create another producers document
  # Invalid document reference - bad JSON
  # Invalid document reference - invalid content (NRL-518)
  # Invalid document reference - invalid context.related for an SSP url
  # Invalid document reference - missing context.related for an SSP url
  # Invalid document reference - invalid docStatus (NRL-477)
  # Invalid document reference - duplicate keys
  # Invalid document reference - duplicate relatesTo targets in URL
  # Invalid document reference - supersede with duplicate error
  # Invalid document reference - missing audit date when permission to set audit date
  # Invalid document reference - SSP URL?
  Scenario: System not supported in NRL 3.0
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property     | value                          |
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
      "diagnostics": "Invalid type system: http://invalidsystem.info/sct Type system must be either 'http://snomed.info/sct' or 'https://nicip.nhs.uk'",
      "expression": ["type.coding[0].system"]
      }
      """

  Scenario: Invalid Document Reference Type
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property     | value                          |
      | subject      | 9999999999                     |
      | status       | current                        |
      | type         | invalid                        |
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

  Scenario Outline: Invalid display value for type or category (imaging)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'ANGY1' is authorised to access pointer types:
      | system               | value |
      | https://nicip.nhs.uk | MAULR |
      | https://nicip.nhs.uk | MAXIB |
    When producer 'ANGY1' creates a DocumentReference with values:
      | property     | value                          |
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

  Scenario: Invalid practice setting (not in value set)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'X26' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'X26' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9999999999                     |
      | status          | current                        |
      | type            | 736253002                      |
      | category        | 734163000                      |
      | custodian       | X26                            |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 12345                          |
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
        "diagnostics": "Invalid practice setting code: 12345 Practice Setting coding must be a member of value set https://fhir.nhs.uk/England/ValueSet/England-PracticeSetting",
        "expression": ["context.practiceSetting.coding[0].code"]
      }
      """

  Scenario: Invalid practice setting (valid code but wrong display value)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'context' is:
      """
      "context": {
      "practiceSetting": {
      "coding": [
      {
      "system": "http://snomed.info/sct",
      "code": "788002001",
      "display": "Ophthalmology service"
      }
      ]
      }
      }
      """
    Then the response status code is 422
    And the response is an OperationOutcome with 1 issue

  Scenario: Missing content
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
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
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
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
    When producer 'ANGY1' creates a DocumentReference with values:
      | property    | value                          |
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
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
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

  Scenario: Invalid content has extra field
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 1363501000000100 |
      | http://snomed.info/sct | 736253002        |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
      """
      "content": [
        {
          "attachment": {
              "contentType": "application/pdf",
              "url": "someContact.co.uk"
          },
          "format": {
              "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
              "code": "urn:nhs-ic:unstructured",
              "display": "Unstructured Document"
          },
          "extra_field": "hello",
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
        "diagnostics": "Request body could not be parsed (content[0].extra_field: Extra inputs are not permitted)",
        "expression": [
          "content[0].extra_field"
        ]
      }
      """

  Scenario: codings with empty string or leading whitespace
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'context' is:
      """
      "context": {
        "practiceSetting": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "788002001",
              "display": ""
            }
          ]
        },
        "facilityType": {
          "coding": [
            {
              "system": " system",
              "code": "1234"
            }
          ]
        }
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
        "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: context.practiceSetting.coding[0].display)",
        "expression": [
          "DocumentReference"
        ]
      }
      """

  Scenario: Reject DocumentReference with empty non-mandatory field (author)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'author' is:
      """
      "author": []
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
        "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: author)",
        "expression": ["DocumentReference"]
      }
      """

  Scenario: RetrievalMechanism extension is empty
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'TSTCUS' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer 'TSTCUS' requests creation of a DocumentReference with default test values except 'content' is:
      """
      "content": [
        {
          "attachment": {
            "contentType": "application/pdf",
            "url": "https://example.org/my-doc.pdf"
          },
          "format": {
            "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
            "code": "urn:nhs-ic:unstructured",
            "display": "Unstructured Document"
          },
          "extension": []
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
        "diagnostics": "Request body could not be parsed (DocumentReference: Value error, The following fields are empty: content[0].extension)",
        "expression": [
          "DocumentReference"
        ]
      }
      """
