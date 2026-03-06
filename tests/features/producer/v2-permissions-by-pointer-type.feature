Feature: Producer v2 permissions by pointer type - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer at the path
  {actorType}/{app_id}/{ods_code}.json, which must contain a "types" array.
  Permissions for the feature test application (ID 'z00z-y11y-x22x') and
  ODS code 'RX898' are baked into the layer by `scripts/get_s3_permissions.py`
  at build time, so no dynamic seeding step is required for
  success scenarios.

  Background:
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API

  Scenario: V2 Permissions with access for pointer type - createDocumentReference
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
      | type            | 736253002                      |
      | category        | 734163000                      |
      | custodian       | RX898                          |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |

  Scenario: V2 Permissions with access for pointer type - deleteDocumentReference
    Given a DocumentReference resource exists with values
      | property    | value                          |
      | id          | RX898-111-DeleteDocRefTest1    |
      | subject     | 9278693472                     |
      | status      | current                        |
      | type        | 736253002                      |
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
    And the resource with id 'DK94-111-DeleteDocRefTest1' does not exist

  Scenario: V2 Permissions with no access for pointer type - searchDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | RX898-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                               |
      | id          | SG4-1111111111-SearchNHSDocRefTest3 |
      | subject     | 9999999999                          |
      | status      | current                             |
      | type        | 1363501000000100                    |
      | category    | 734163000                           |
      | contentType | application/pdf                     |
      | url         | https://example.org/my-doc.pdf      |
      | custodian   | SG4                                 |
      | author      | X26                                 |
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
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc.pdf        |
      | custodian   | RX898                                 |
      | author      | X26                                   |
    And the Bundle does not contain a DocumentReference with ID 'SG4-1111111111-SearchNHSDocRefTest3'
