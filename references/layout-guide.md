# Flowchart Layout Guide

This skill handles flowcharts with the following characteristics:

## Supported Layout Types

### 1. Swimlane (Primary)
```
| Customer Journey | [Card 1]             | [Card 3]        |
| Partner          |       [Card 2]       |      [Card 4]   |
| Deal Desk        |             [Card 5] |                 |
```

Lanes run horizontally from left to right. Lane labels appear in the left sidebar area and determine the **Role** column.

### 2. Grid (Fallback)
```
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Card 1    │→ │  Card 2    │→ │  Card 3    │
└────────────┘  └────────────┘  └────────────┘
     ↓               ↓               ↓
┌────────────┐  ┌────────────┐  ┌────────────┐
│  Card 4    │→ │  Card 5    │→ │  Card 6    │
└────────────┘  └────────────┘  └────────────┘
```

Cards in a 2-row grid with optional lane labels. Cards are ordered left-to-right, top-to-bottom.

## Step Card Detection

Step cards are **shaded blue rectangles** detected via connected-component analysis:

- **Blue threshold**: b > r+30 AND b > g+30 AND b > 100
- **Size range**: Width 50–250px, Height 25–100px (adjustable)
- Cards must be horizontally aligned (sufficient blue pixels in center row)

## Card Contents

Each card typically contains:

1. **Step text** (center area → **Step** column) — e.g. "Send Prepopulated Deck"
2. **System text** (below the card → **System** column) — e.g. "CRM", "SAP BPC"
3. **Description** (full card text → **Activity** column) — detailed step description
4. **Role/actor** (external labels, lane labels, or inherited → **Role** column)

## Automation Detection

Icons on each card determine the **Automated or Manual** column:

- **Auto**: Gear/cog icon → center density check detects hollow center
- **Manual**: Person/user icon → solid center or no icon detected
- **None**: No detectable icon → blank

## Lane Labels

Left-side lane/role labels are detected by scanning the left sidebar (x=0–200px) for text clusters grouped by y-range. These map to the **Role** column via the 5-level priority system.
