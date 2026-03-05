Feature: Consumer v2 permissions by pointer type - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer at the path
  {actorType}/{app_id}/{ods_code}.json, which must contain a "types" array.
  Permissions for the feature test application (ID 'z00z-y11y-x22x') and
  ODS code 'RX898' are baked into the layer by `scripts/get_s3_permissions.py`
  at build time, so no dynamic seeding step is required for
  success scenarios.

  Background:
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API

  Scenario: V2 Permissions with access for pointer type - readDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                      |
      | id          | RX898-9999999999-ReadDocRefV2SameCustodian |
      | subject     | 9999999999                                 |
      | status      | current                                    |
      | type        | 736253002                                  |
      | category    | 734163000                                  |
      | contentType | application/pdf                            |
      | url         | https://example.org/my-doc.pdf             |
      | custodian   | RX898                                      |
      | author      | RX898                                      |
    When consumer v2 'RX898' reads a DocumentReference with ID 'RX898-9999999999-ReadDocRefV2SameCustodian'
    Then the response status code is 200
    And the response is a DocumentReference with JSON value:
      """
      {
        "resourceType": "DocumentReference",
        "id": "RX898-9999999999-ReadDocRefV2SameCustodian",
        "status": "current",
        "type": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "736253002",
              "display": "Mental health crisis plan"
            }
          ]
        },
        "category": [
          {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "734163000",
                "display": "Care plan"
              }
            ]
          }
        ],
        "subject": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/nhs-number",
            "value": "9999999999"
          }
        },
        "custodian": {
          "identifier": {
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            "value": "RX898"
          }
        },
        "author": [
          {
            "identifier": {
              "system": "https://fhir.nhs.uk/Id/ods-organization-code",
              "value": "RX898"
            }
          }
        ],
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
              },
              {
                "url": "https://fhir.nhs.uk/England/StructureDefinition/Extension-England-NRLRetrievalMechanism",
                "valueCodeableConcept": {
                  "coding": [
                    {
                      "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLRetrievalMechanism",
                      "code": "Direct",
                      "display": "Direct"
                    }
                  ]
                }
              }
            ]
          }
        ],
        "context": {
          "practiceSetting": {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "788007007",
                "display": "General practice service"
              }
            ]
          }
        }
      }
      """

  Scenario: V2 permissions with access for pointer type retrieves expected document references - searchPostDocumentReference
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                             |
      | id          | X26-1111111111-SearchMultipleRefTestDifferentType |
      | subject     | 9278693472                                        |
      | status      | current                                           |
      | type        | 887701000000100                                   |
      | category    | 734163000                                         |
      | contentType | application/pdf                                   |
      | url         | https://example.org/my-doc-3.pdf                  |
      | custodian   | X26                                               |
      | author      | X26                                               |
    When consumer v2 'RX898' searches for DocumentReferences using POST with request body:
      | key     | value      |
      | subject | 9278693472 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 2
    And the Bundle has 2 entries
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'X26-1111111111-SearchMultipleRefTestDifferentType'

  Scenario: V2 permissions with no access for pointer type - searchDocumentReference
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer v2 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                                   |
      | subject   | 9278693472                              |
      | type      | http://snomed.info/sct\|887701000000100 |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "code-invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "INVALID_CODE_SYSTEM",
            "display": "Invalid code system"
          }]
        },
        "diagnostics": "Invalid query parameter (The provided type does not match the allowed types for this organisation)",
        "expression": ["type"]
      }
      """
