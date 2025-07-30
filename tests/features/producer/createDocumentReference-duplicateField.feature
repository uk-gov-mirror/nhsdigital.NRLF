Feature: Producer - createDocumentReference - Duplicate Field Scenarios

  Scenario: Duplicate url field in attachment
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
              "url": "https://example.org/my-doc.pdf",
              "url": "https://example.org/duplicate-url.pdf"
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
        "diagnostics": "Duplicate keys found in FHIR document: ['url']",
        "expression": [
            "DocumentReference.content[0].attachment.url"
        ]
      }
      """

  Scenario: Duplicate format and attachement field in content
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
          "attachment": {
              "contentType": "text/html",
              "url": "https://example.org/contact-details.html"
          },
          "format": {
              "system": "https://fhir.nhs.uk/England/CodeSystem/England-NRLFormatCode",
              "code": "urn:nhs-ic:unstructured",
              "display": "Unstructured Document"
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
        "diagnostics": "Duplicate keys found in FHIR document: ['attachment', 'format']",
        "expression": [
            "DocumentReference.content[0].attachment",
            "DocumentReference.content[0].format"
        ]
      }
      """
