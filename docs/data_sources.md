# Data sources

## Wikivoyage (CC BY-SA 4.0)

This project fetches destination content from Wikivoyage and stores it locally for retrieval-augmented generation (RAG).

Wikivoyage text is licensed under Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0).
We store, for every chunk:
- page_title
- source_url (permalink with revision id when available)
- attribution string: "Source: Wikivoyage (CC BY-SA 4.0), page: <TITLE>"

When returning RAG results, the API includes citations using the stored source_url and attribution.
