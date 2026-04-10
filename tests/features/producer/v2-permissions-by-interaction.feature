Feature: Producer v2 permissions by pointer type - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer.  Permissions for the feature tests are baked into the layer by
  `scripts/get_s3_permissions.py` at build time, so no dynamic seeding step is required for
  success scenarios.

  Background:
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API

  Scenario: V2 Permissions with no access for producer interaction - createDocumentReference
    When producer '1DSYNCTEST' creates a DocumentReference with values:
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
              "code": "ACCESS DENIED",
              "display": "Access has been denied to process this request"
            }
          ]
        },
        "diagnostics": "Your organisation '1DSYNCTEST' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: V2 Permissions with all Producer perms has no access for upsert - upsertDocumentReference
    Given a DocumentReference resource exists with values:
      | property    | value                                |
      | id          | ODS1-1111111111-SearchNHSDocRefTest1 |
      | subject     | 9999999999                           |
      | status      | current                              |
      | type        | 736373009                            |
      | category    | 734163000                            |
      | contentType | application/pdf                      |
      | url         | https://example.org/my-doc.pdf       |
      | custodian   | ODS1                                 |
      | author      | X26                                  |
    When producer 'ODS1' upserts a DocumentReference with values:
      | property  | value                                |
      | id        | ODS1-1111111111-SearchNHSDocRefTest1 |
      | subject   | 9999999999                           |
      | status    | current                              |
      | type      | 736373009                            |
      | category  | 734163000                            |
      | url       | https://example.org/my-doc.pdf       |
      | custodian | ODS1                                 |
      | author    | X26                                  |
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
        "diagnostics": "Your organisation 'ODS1' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: V2 Permissions with internal perms has access for upsert - upsertDocumentReference
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation '1DSYNCTEST' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When producer '1DSYNCTEST' upserts a DocumentReference with values:
      | property  | value                              |
      | id        | 1DSYNCTEST-testid-upsert-0001-0001 |
      | subject   | 9278693472                         |
      | status    | current                            |
      | type      | 736253002                          |
      | category  | 734163000                          |
      | custodian | 1DSYNCTEST                         |
      | author    | HAR1                               |
      | url       | https://example.org/my-doc.pdf     |
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
    And the Document Reference '1DSYNCTEST-testid-upsert-0001-0001' exists with values:
      | property  | value                              |
      | id        | 1DSYNCTEST-testid-upsert-0001-0001 |
      | subject   | 9278693472                         |
      | status    | current                            |
      | type      | 736253002                          |
      | category  | 734163000                          |
      | custodian | 1DSYNCTEST                         |
      | author    | HAR1                               |
      | url       | https://example.org/my-doc.pdf     |
