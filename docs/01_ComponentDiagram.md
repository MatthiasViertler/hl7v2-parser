# Component Architecture

This diagram shows the major subsystems of the HL7v2 engine and how they interact during message ingestion, validation, routing, and storage. 
It provides a structural overview of the system before diving into routing and validation specifics.

The components are intentionally modular so each part can be tested, replaced, or extended independently.

## ASCII Diagram


See also:
- [Routing Logic](02_RoutingLogicDiagram.md)
- [Validation Pipeline](03_ValidationPipeline.md)

## Component Diagram

                   ┌──────────────────────────┐
                   │        MLLP Client        │
                   └──────────────┬────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────┐
                   │       MLLP Server        │
                   │  hl7engine/mllp_server   │
                   └──────────────┬────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────┐
                   │       HL7 Listener       │
                   │  hl7engine/hl7_listener  │
                   └──────────────┬────────────┘
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
┌──────────────┐          ┌──────────────┐          ┌────────────────┐
│    Parser    │          │  Validator   │          │    Router      │
│ parse_hl7.py │          │ validator.py │          │   router.py    │
└──────┬───────┘          └──────┬──────┘          └──────┬─────────┘
       │                          │                         │
       ▼                          ▼                         ▼
┌──────────────┐          ┌──────────────┐          ┌────────────────┐
│   Database   │          │   REST API   │          │  Routed Files  │
│    db.py     │          │    api.py    │          │   routed/...   │
└──────────────┘          └──────────────┘          └────────────────┘

## Mermaid Version

```mermaid
flowchart TD

    A[MLLP Client] --> B[MLLP Server<br/>hl7engine/mllp_server]

    B --> C[HL7 Listener<br/>hl7engine/hl7_listener]

    C --> D[Parser<br/>parse_hl7.py]
    C --> E[Validator<br/>validator.py]
    C --> F[Router<br/>router.py]
    C --> G[Database<br/>db.py]
    C --> H[REST API<br/>api.py]

    F --> I[Routed Files<br/>routed/]
    G --> J[SQLite DB<br/>data/hl7_messages.db]
```
