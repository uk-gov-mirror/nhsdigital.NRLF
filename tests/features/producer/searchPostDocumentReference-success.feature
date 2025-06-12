Feature: Producer - searchPostDocumentReference - Success Scenarios

  Scenario: Search for multiple DocumentReferences by NHS number and Summary
    Given the application 'DataShare' (ID 'z00z-y11y-x22x') is registered to access the API
    And the organisation 'RX898' is authorised to access pointer types:
      | system                 | value            |
      | http://snomed.info/sct | 736253002        |
      | http://snomed.info/sct | 1363501000000100 |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest1 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-1.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | X26-1111111111-SearchMultipleRefTest2 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 736253002                             |
      | category    | 734163000                             |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-2.pdf      |
      | custodian   | X26                                   |
      | author      | X26                                   |
    And a DocumentReference resource exists with values:
      | property    | value                                 |
      | id          | x26-1111111111-SearchMultipleRefTest3 |
      | subject     | 9278693472                            |
      | status      | current                               |
      | type        | 1363501000000100                      |
      | category    | 1102421000000108                      |
      | contentType | application/pdf                       |
      | url         | https://example.org/my-doc-3.pdf      |
      | custodian   | x26                                   |
      | author      | x26                                   |
    When producer 'RX898' searches for DocumentReferences using POST with request body:
      | key      | value      |
      | subject  | 9278693472 |
      | _summary | count      |
    Then the response status code is 200
    And the response is a searchset Bundle
    And the Bundle has a total of 3
