Feature: Consumer - HEAD Requests

  Scenario Outline: DocumentReference with HEAD fails (Content-Type: <content_type>)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' sends HEAD request to 'DocumentReference' endpoint with headers:
      | header       | value          |
      | Content-Type | <content_type> |
    Then the response status code is 405
    And the response has an empty body
    And the Allow header is 'GET'
    And the Content-Length header is '0'

    Examples:
      | content_type          |
      | application/json      |
      | application/json+fhir |
      | application/fhir+json |

  Scenario Outline: DocumentReference/{id} with HEAD fails (Content-Type: <content_type>)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' sends HEAD request to 'DocumentReference/random-id' endpoint with headers:
      | header       | value          |
      | Content-Type | <content_type> |
    Then the response status code is 405
    And the response has an empty body
    And the Allow header is 'GET'
    And the Content-Length header is '0'

    Examples:
      | content_type          |
      | application/json      |
      | application/json+fhir |
      | application/fhir+json |

  Scenario Outline: DocumentReference with HEAD fails with 415 with unsupported (Content-Type: <content_type>)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' sends HEAD request to 'DocumentReference' endpoint with headers:
      | header       | value          |
      | Content-Type | <content_type> |
    Then the response status code is 415
    And the Content-Type header is 'application/json'
    And the Content-Length header is '0'
    And the Allow header is not present

    Examples:
      | content_type             |
      | application/notsupported |
      | application/helloworld   |
      | application/harold       |

  Scenario Outline: DocumentReference/{id} with HEAD fails (Content-Type: <content_type>)
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' sends HEAD request to 'DocumentReference/random-id' endpoint with headers:
      | header       | value          |
      | Content-Type | <content_type> |
    Then the response status code is 415
    And the response has an empty body
    And the Content-Type header is 'application/json'
    And the Content-Length header is '0'
    And the Allow header is not present

    Examples:
      | content_type             |
      | application/notsupported |
      | application/helloworld   |
      | application/harold       |
