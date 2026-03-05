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

  Scenario: Successfully create a Document Pointer (care plan)
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
