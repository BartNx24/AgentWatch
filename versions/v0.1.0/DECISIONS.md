# AgentWatch design decisions

All decisions below describe this initial starter created on 29 October 2026. They are proposed implementation choices for group review.

## D1 Keep the first prototype easy to run

Use Python's standard library for the first local pilot. SQLite and unittest are included with Python. FastAPI, pandas and pytest remain available for a subsequent iteration consistent with the proposed architecture. The pilot tests authorization behavior before adding an API interface.

## D2 Use six balanced scenario categories

Use the six categories with five cases each from Objective 3: technically authorized and task-appropriate low/high risk; technically unauthorized low/high risk; technically authorized but task-inappropriate low/high risk. Each case is run under every strategy. Each run starts with an independent copy of the same mock workspace.

## D3 Keep decisions separate from expected labels

Technical authorization is calculated from the resource/action grants. Task appropriateness is calculated from allowed actions, resource scope and recipient scope. High-risk actions include deletion, sharing and exporting, plus all operations on records labelled confidential. The runtime policy does not consult the ground_truth, category or expected_decisions fields.

These task scopes and risk rules are explicitly supplied by the experiment designer. The prototype does not automatically infer intent from natural language, detect prompt injection, or assess policy quality outside the declared cases.

## D4 Enforce approval order

Under combined controls, deny a request without technical permission, then deny a request outside the assigned task. An eligible high-risk request is pending until scripted approval is granted. Approval refusal does not execute the action. An approval cannot override a block or be resolved twice.

## D5 Separate measured and simulated timing

Measure the local decision, mock execution and approval-resolution processing. Record a chosen approval waiting time separately. Estimated total time is measured processing time plus the assumed delay. No real human waiting time is observed and no deliberate sleep is used.

## D6 State the comparison's limits

The combined condition adds both task context and approval. Its comparison with permission checks alone estimates their combined difference in these predefined scenarios. A fourth condition with permissions and context but no approval would be needed to isolate approval's incremental effect; adding it would require revising the protocol and run count.

No external AI service, real company files or actual message delivery is involved. Successful tests show that this code follows its declared rules in the tested cases. They are not evidence of general security effectiveness against real autonomous agents.
