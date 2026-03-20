Feature: Producer v2 permissions by pointer type - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer.  Permissions for the feature tests are baked into the layer by
  `scripts/get_s3_permissions.py` at build time, so no dynamic seeding step is required for
  success scenarios.

  Background:
    Given the application 'DataShare' (ID 'v2-z00z-y11y-x22x') is registered to access the API

  Scenario: V2 Permissions with access for pointer type - createDocumentReference
    When producer v2 'RX898' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736373009                      |
      | category        | 734163000                      |
      | custodian       | RX898                          |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |
    Then the response status code is 201
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
      "severity": "information",
      "code": "informational",
      "details": {
      "coding": [
      {
      "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
      "code": "RESOURCE_CREATED",
      "display": "Resource created"
      }
      ]
      },
      "diagnostics": "The document has been created"
      }
      """
    And the response has a Location header
    And the Location header starts with '/DocumentReference/RX898-'
    And the resource in the Location header exists with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736373009                      |
      | category        | 734163000                      |
      | custodian       | RX898                          |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |

  Scenario: V2 Permissions with no access for pointer type - createDocumentReference
    When producer v2 'RX898' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736253002                      |
      | category        | 734163000                      |
      | custodian       | RX898                          |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |
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

  Scenario: V2 Permissions with access for pointer type - deleteDocumentReference
    Given a DocumentReference resource exists with values
      | property    | value                          |
      | id          | RX898-111-DeleteDocRefTest1    |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 736373009                      |
      | category    | 734163000                      |
      | contentType | application/pdf                |
      | url         | https://example.org/my-doc.pdf |
      | custodian   | RX898                          |
      | author      | RX898                          |
    When producer v2 'RX898' requests to delete DocumentReference with id 'RX898-111-DeleteDocRefTest1'
    Then the response status code is 200
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "information",
        "code": "informational",
        "details": {
          "coding": [
            {
              "system": "https://fhir.nhs.uk/ValueSet/NRL-ResponseCode",
              "code": "RESOURCE_DELETED",
              "display": "Resource deleted"
            }
          ]
        },
        "diagnostics": "The requested DocumentReference has been deleted"
      }
      """
    And the resource with id 'RX898-111-DeleteDocRefTest1' does not exist

  Scenario: V2 Permissions search results are scoped to allowed pointer types - searchDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736373009                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 1363501000000100                      |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    When producer v2 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9999999999 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 1
    And the Bundle has 1 entry
    And the Bundle contains an DocumentReference with values
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736373009                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'RX898-1111111111-SearchNHSDocRefTest2'

  Scenario: V2 Permissions search results for allow_all_types - searchDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736373009                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | 4LLTYP35P                             |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 1363501000000100                      |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | 4LLTYP35P                             |
      | author      | X26                                   |
    When producer v2 '4LLTYP35P' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9999999999 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 2
    And the Bundle has 2 entries
    And the Bundle contains an DocumentReference with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736373009                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | 4LLTYP35P                             |
      | author      | X26                                   |
    And the Bundle contains an DocumentReference with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest2 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 1363501000000100                      |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | 4LLTYP35P                             |
      | author      | X26                                   |

  Scenario: V2 Permissions with no access for org - searchDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736373009                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    When producer v2 'N00RG1' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9999999999 |
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
        "diagnostics": "Your organisation 'N00RG1' does not have permission to access this resource. Contact the onboarding team."
      }
      """
