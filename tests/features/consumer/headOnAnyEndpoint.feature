Feature: Consumer - HEAD Requests

  @custom_tag
  Scenario: DocumentReference with HEAD fails
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    When consumer 'RX898' sends HEAD request to DocumentReference endpoint
    Then the response status code is 405
    And the response has an empty body
    And the Allow header is 'GET'
