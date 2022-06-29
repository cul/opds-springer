ToDos and Questions
===================

## CUL/DIAG
- dump subjects
- dump contributors
- dump identifiers
## Springer
- no transactional way to crawl, and sort means dataset will change underneath you. Recommendation?
- subject vocabulary not identified - is there one?
- subjects not available in docs, expensive to grab
- subject priority ("primary subject") only available in CSV export
- genre vocabulary not identified
- publisher vs copyright data, which sometimes includes print publisher
- single-document timeouts killing a batch retrieval
- deeply nested responses e.g. 10.1007/978-3-319-67816-0
- all API responses apear to have `"openaccess": "false"`, even when text is also in OAPEN/DOAB (cf 978-3-030-13864-6 https://clio.columbia.edu/catalog/14350933/librarian_view)
## Lyrasis
- no genre representation in OPDS - how to communicate?
- no EISBN/ISBN distinction - does this matter?
- where to include copyright notes in opds?
- Should Springer subjects be a scheme? How then to identify?
- WAYFLESS URL templates: Springer's has SAML id. What variables are available?
- Is there a way to share subject lookups between Palace instances? API key rate limits may be prohibitive.
