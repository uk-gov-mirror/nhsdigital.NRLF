Feature: Producer v2 APP-LEVEL permissions by pointer type - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer.  Permissions for the feature tests are baked into the layer by
  `scripts/get_s3_permissions.py` at build time, so no dynamic seeding step is required for
  success scenarios.

  Scenario: HAPPY PATH V2 Permissions with access for pointer type - createDocumentReference
    Given the application 'ProducerTest001' (ID 'app-t001') is registered to access the API
    When producer v2 'ORGA' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 861421000000109                |
      | category        | 734163000                      |
      | custodian       | ORGA                           |
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
    And the Location header starts with '/DocumentReference/ORGA-'
    And the resource in the Location header exists with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 861421000000109                |
      | category        | 734163000                      |
      | custodian       | ORGA                           |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |

  Scenario: V2 Permissions with no producer access at all (but app level consumer access for specified type)
    Given the application 'ProducerTest002' (ID 'app-t002') is registered to access the API
    When producer v2 'ORGA' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736366004                      |
      | category        | 734163000                      |
      | custodian       | ORGA                           |
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
        "diagnostics": "Your organisation 'ORGA' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: V2 Permissions with no access to specified type
    Given the application 'ProducerTest003' (ID 'app-t003') is registered to access the API
    When producer v2 'ORGA' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 749001000000101                |
      | category        | 419891008                      |
      | custodian       | ORGA                           |
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

  Scenario: V2 Permissions with org-level permissions for requested type but app level permissions for other types
    Given the application 'ProducerTest004' (ID 'app-t004') is registered to access the API
    When producer v2 'ODS1' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 2181441000000107               |
      | category        | 734163000                      |
      | custodian       | ODS1                           |
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
