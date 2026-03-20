Feature: Producer v2 access_control permissions - Success and Failure Scenarios

  Scenario: Successfully create a DocumentReference with a specified date with the ALLOW_OVERRIDE_CREATION_DATETIME permission - createDocumentReference
    Given the application 'DataShare' (ID 'v2-z00z-y11y-x22x') is registered to access the API
    When producer '4LLTYP35P' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736253002                      |
      | category        | 734163000                      |
      | custodian       | 4LLTYP35P                      |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |
      | date            | 2024-06-01T12:00:00Z           |
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
    And the Location header starts with '/DocumentReference/4LLTYP35P-'
    And the resource in the Location header exists with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736253002                      |
      | category        | 734163000                      |
      | custodian       | 4LLTYP35P                      |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |
      | date            | 2024-06-01T12:00:00Z           |

  Scenario: Create a DocumentReference with a specified date WITHOUT ALLOW_OVERRIDE_CREATION_DATETIME - date should be overridden by the server
    Given the application 'DataShare' (ID 'v2-z00z-y11y-x22x') is registered to access the API
    When producer 'RX898' creates a DocumentReference with values:
      | property        | value                          |
      | subject         | 9278693472                     |
      | status          | current                        |
      | type            | 736373009                      |
      | category        | 734163000                      |
      | custodian       | RX898                          |
      | author          | HAR1                           |
      | url             | https://example.org/my-doc.pdf |
      | practiceSetting | 788002001                      |
      | date            | 2024-06-01T12:00:00Z           |
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
    And the date of the resource in the Location header is not '2024-06-01T12:00:00Z'

  Scenario: Successfully supersede a DocumentReference with ALLOW_SUPERSEDE_WITH_DELETE_FAILURE - upsertDocumentReference
    Given the application 'DataShare' (ID 'v2-z00z-y11y-x22x') is registered to access the API
    When producer '4LLTYP35P' upserts a DocumentReference with values:
      | property   | value                                          |
      | id         | 4LLTYP35P-testid-upsert-0001-0002              |
      | subject    | 9278693472                                     |
      | status     | current                                        |
      | type       | 736253002                                      |
      | category   | 734163000                                      |
      | custodian  | 4LLTYP35P                                      |
      | author     | 4LLTYP35P                                      |
      | url        | https://example.org/newdoc.pdf                 |
      | supercedes | 4LLTYP35P-000-ThisRefDoesNotExistSupersedeTest |
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
               "code": "RESOURCE_SUPERSEDED",
               "display": "Resource created and resource(s) deleted"
             }
           ]
         },
         "diagnostics": "The document has been superseded by a new version"
       }
      """

  Scenario: Supersede a DocumentReference fails without ALLOW_SUPERSEDE_WITH_DELETE_FAILURE - createDocumentReference
    Given the application 'DataShare' (ID 'v2-z00z-y11y-x22x') is registered to access the API
    When producer 'RX898' creates a DocumentReference with values:
      | property   | value                                      |
      | subject    | 9278693472                                 |
      | status     | current                                    |
      | type       | 736373009                                  |
      | category   | 734163000                                  |
      | custodian  | RX898                                      |
      | author     | RX898                                      |
      | url        | https://example.org/newdoc.pdf             |
      | supercedes | RX898-000-ThisRefDoesNotExistSupersedeTest |
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
        "diagnostics": "The relatesTo target document does not exist",
        "expression": [
            "relatesTo[0].target.identifier.value"
        ]
      }
      """
