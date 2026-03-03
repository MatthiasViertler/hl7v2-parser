# Routing Logic

This diagram illustrates how the router determines the correct output folder for each HL7 message based on `msg_type` and `trigger` using `routes.yaml`.

## ASCII Version
                   ┌──────────────────────────────┐
                   │   Parsed HL7 Message         │
                   │  (msg_type, trigger, ctrl)   │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │       routes.yaml             │
                   │   e.g. ORU: R01: routed/...   │
                   └──────────────┬───────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
   Does msg_type exist?   Does trigger exist?   Use fallback folder
             │                    │                    │
             ▼                    ▼                    ▼
     routed/<msg_type>/   routed/<msg_type>/<trigger>/ routed/<msg_type>/
             │                    │                    │
             └──────────────┬─────┴───────┬──────────┘
                            ▼             ▼
                     Write file:   <control_id>.hl7

## Mermaid Version
```mermaid
flowchart TD

    A[Parsed HL7 (msg_type, trigger, control_id)] --> B[Load routes.yaml]

    B --> C{msg_type defined?}
    C -- No --> Z[Fallback folder]
    C -- Yes --> D{trigger defined?}

    D -- Yes --> E[Use routed/msg_type/trigger]
    D -- No --> F[Use routed/msg_type]

    E --> G[Write control_id.hl7]
    F --> G


```
