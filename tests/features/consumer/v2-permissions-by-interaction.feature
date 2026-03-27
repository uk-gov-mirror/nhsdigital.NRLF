Feature: Consumer v2 permissions by interaction - Success and Failure Scenarios
  For the v2 permissions model, permissions are resolved from a JSON file stored in the
  nrlf_permissions Lambda layer.  Permissions for the feature tests are baked into the layer
  by `scripts/get_s3_permissions.py` at build time, so no dynamic seeding step is required for
  success scenarios.

  Background:
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API

  Scenario: V2 permissions with no access for interaction - searchDocumentReference
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer v2 '1DSYNC1NT3R4CT1ON5' searches for DocumentReferences with parameters:
      | parameter | value                                   |
      | subject   | 9278693472                              |
      | type      | http://snomed.info/sct\|887701000000100 |
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
        "diagnostics": "Your organisation '1DSYNC1NT3R4CT1ON5' does not have permission to access this resource. Contact the onboarding team."
      }
      """
