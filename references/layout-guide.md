# Flowchart Layout Guide

This skill expects flowcharts with the following layout:

```
┌────────────┐  ┌────────────┐  ┌────────────┐
│            │  │            │  │            │
│  Card 1    │→ │  Card 2    │→ │  Card 3    │
│  (Top-L)   │  │  (Top-M)   │  │  (Top-R)   │
│            │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘
     ↓               ↓               ↓
┌────────────┐  ┌────────────┐  ┌────────────┐
│            │  │            │  │            │
│  Card 4    │→ │  Card 5    │→ │  Card 6    │
│  (Bot-L)   │  │  (Bot-M)   │  │  (Bot-R)   │
│            │  │            │  │            │
└────────────┘  └────────────┘  └────────────┘
```

## Coordinate Map (pixels)

| Region | x1 | y1 | x2 | y2 |
|--------|----|----|----|----|
| Card 1 (Top-Left) | 310 | 120 | 440 | 225 |
| Card 2 (Top-Mid) | 480 | 120 | 615 | 225 |
| Card 3 (Top-Right) | 660 | 120 | 800 | 225 |
| Card 4 (Bot-Left) | 310 | 240 | 440 | 340 |
| Card 5 (Bot-Mid) | 480 | 240 | 615 | 340 |
| Card 6 (Bot-Right) | 660 | 240 | 800 | 340 |
| Left Lane Row 1 | 86 | 55 | 310 | 215 |
| Left Lane Row 2 | 86 | 215 | 310 | 335 |

## Card Contents

Each card typically contains:

1. **Step name** (top area → L4) — e.g. "Receive Customer Complaint"
2. **System name** (bottom area → System) — e.g. "CRM", "ERP"
3. **Description** (middle area → L5) — full step text
4. **Role/actor** (sometimes explicit in text → Role)
