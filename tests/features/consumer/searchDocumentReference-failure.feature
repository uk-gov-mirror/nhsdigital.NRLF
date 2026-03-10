Feature: Consumer - searchDocumentReference - Failure Scenarios

  Scenario: Search fails to return a bundle when extra parameters are found
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
      | extra     | parameter  |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "INVALID_PARAMETER",
            "display": "Invalid parameter"
          }]
        },
        "diagnostics": "Invalid query parameter (extra: Extra inputs are not permitted)",
        "expression": ["extra"]
      }
      """

  Scenario: Search fails to return a bundle when no subject:identifier is provided
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "INVALID_PARAMETER",
            "display": "Invalid parameter"
          }]
        },
        "diagnostics": "Invalid query parameter (subject:identifier: Field required)",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Search rejects request with type system they are not allowed to use
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                                |
      | subject   | 9278693472                           |
      | type      | http://incorrect.info/sct\|736253002 |
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

  Scenario: Search rejects request with type they are not allowed to use
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
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

  Scenario: Search rejects request when the NHS number provided is invalid
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value |
      | subject   | 123   |
    Then the response status code is 400
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "invalid",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "INVALID_NHS_NUMBER",
            "display": "Invalid NHS number"
          }]
        },
        "diagnostics": "A valid NHS number is required to search for document references",
        "expression": ["subject:identifier"]
      }
      """

  Scenario: Search rejects request if the organisation has no registered pointer types
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system | value |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "ACCESS DENIED",
            "display": "Access has been denied to process this request"
          }]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Search rejects request if the organisation has no registered pointer types but uses category filter
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system | value |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                             |
      | subject   | 9278693472                        |
      | category  | http://snomed.info/sct\|734163000 |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "ACCESS DENIED",
            "display": "Access has been denied to process this request"
          }]
        },
        "diagnostics": "Your organisation 'RX898' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Search returns no results if category filter is used without any relevant type permissions
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    And a DocumentReference resource exists with values:
      | property    | value                            |
      | id          | 8FW23-537854543-SearchDocRefTest |
      | subject     | 9278693472                       |
      | status      | current                          |
      | type        | 1363501000000100                 |
      | category    | 1102421000000108                 |
      | contentType | application/pdf                  |
      | url         | https://example.org/my-doc.pdf   |
      | custodian   | 8FW23                            |
      | author      | 8FW23                            |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                                    |
      | subject   | 9278693472                               |
      | category  | http://snomed.info/sct\|1102421000000108 |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a self link matching 'DocumentReference?subject:identifier=https://fhir.nhs.uk/Id/nhs-number|9278693472&category=http://snomed.info/sct|1102421000000108'
    And the Bundle has a total of 0
    And the Bundle has 0 entries

  Scenario: Search gives 403 if no permission
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And a DocumentReference resource exists with values:
      | property    | value                             |
      | id          | 8FW23-1114567890-SearchDocRefTest |
      | subject     | 9278693472                        |
      | status      | current                           |
      | type        | 736253002                         |
      | category    | 734163000                         |
      | contentType | application/pdf                   |
      | url         | https://example.org/my-doc.pdf    |
      | custodian   | 8FW23                             |
      | author      | 8FW23                             |
    When consumer v1 'Z26' searches for DocumentReferences with parameters:
      | parameter | value      |
      | subject   | 9278693472 |
      | type      | 736253002  |
    Then the response status code is 403
    And the response is an OperationOutcome with 1 issue
    And the OperationOutcome contains the issue:
      """
      {
        "severity": "error",
        "code": "forbidden",
        "details": {
          "coding": [{
            "system": "https://fhir.nhs.uk/CodeSystem/Spine-ErrorOrWarningCode",
            "code": "ACCESS DENIED",
            "display": "Access has been denied to process this request"
          }]
        },
        "diagnostics": "Your organisation 'Z26' does not have permission to access this resource. Contact the onboarding team."
      }
      """

  Scenario: Search rejects request with invalid category system
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                                |
      | subject   | 9278693472                           |
      | category  | http://incorrect.info/sct\|736253002 |
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
        "diagnostics": "Invalid query parameter (The provided category is not valid)",
        "expression": ["category"]
      }
      """

  Scenario: Search rejects request with multiple categories and one invalid category
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value     |
      | http://snomed.info/sct | 736253002 |
    When consumer v1 'RX898' searches for DocumentReferences with parameters:
      | parameter | value                                                             |
      | subject   | 9278693472                                                        |
      | category  | http://snomed.info/sct\|734163000,http://snomed.info/sct\|invalid |
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
        "diagnostics": "Invalid query parameter (The provided category is not valid)",
        "expression": ["category"]
      }
      """
