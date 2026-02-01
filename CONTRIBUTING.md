# Contribution Guidelines

This repository is maintained by the National Record Locator team within the Transformation Directorate of NHS England. 
We welcome contributions from other teams. 

## Raising an Issue

If you raise an issue against this repository, please include as much information as possible to reproduce any bugs,
or specific locations in the case of content errors.

## Contributing Code

To contribute code, please raise a pull request.

Ideally pull requests should be fairly granular and aim to solve one problem each. It would also be helpful if they
linked to an issue. If the maintainers cannot understand why a pull request was raised, it will be rejected,
so please explain why the changes need to be made (unless it is self-evident) or reference the issue they solve. 

Code owners are notified daily about any pending pull requests via automated tools. If your pull request is not 
yet ready for review, please consider keeping it marked as a Draft. 

### Naming and committing conventions

Branch names should be of the format:

`feature/[Shortcode]-[Jira-ref]-short-issue-description`
e.g.
`feature/shco1-NRL-123-contribution-guidelines`

Multiple branches are permitted for the same ticket. 

Please include the Jira reference in your commit messages. 

Your pull request title should include the ticket reference and a short summary of the change; 
these are used to compile the release notes for each iteration. 

## Specification Changes

If your submission changes the behaviour of the NRL, please consider whether the user-facing documentation 
should be updated at the same time to reflect these changes. There are two related repositories containing 
the specifications [for Producers](https://digital.nhs.uk/developer/api-catalogue/national-record-locator-fhir/v3/producer) 
and [Consumers](https://digital.nhs.uk/developer/api-catalogue/national-record-locator-fhir/v3/consumer) 
of NRL pointers, respectively: 
- [NRL Producer API](https://github.com/NHSDigital/nrl-producer-api)
- [NRL Consumer API](https://github.com/NHSDigital/nrl-consumer-api)
