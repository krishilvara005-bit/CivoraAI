# CIVORA AI PLATFORM — ARCHITECTURAL & ENGINEERING WORKSTATION
### Automated 2D Floor Plan AI Verification: Structural Safety, Cost Estimation & Vastu Shastra Compliance

---

## 1. Executive Summary & Overview

**Civora AI** is a multi-tier engineering and architectural intelligence platform designed to evaluate residential construction plans before ground is broken. The platform ingests 2D architectural drawings (JPG, PNG, PDF, WEBP, DXF, DWG) and automatically extracts spatial, geometrical, and structural parameters using computer vision and optical character recognition (OCR). 

The derived building model is analyzed simultaneously across three specialized engineering domains:
1. **Structure Plan Analyzer**: Evaluates structural viability, load paths, structural dimensions, room inventory, building height, and safety compliance indices against the National Building Code (NBC 2016) and Bureau of Indian Standards (IS 456:2000, IS 1893:2016, IS 875:1987, IS 13920:2016).
2. **Cost Estimation Analyzer**: Generates itemized Bill of Quantities (BOQ), material-wise cost splits (cement, steel, sand, aggregate, masonry, finishes), labour trade breakdowns, floor-wise and room-wise expenditure allocations, AI range predictions, and GST tax calculations calibrated to CPWD Schedule of Rates.
3. **Vastu Shastra AI Workstation**: Implements an 8-directional spatial mandala analysis evaluating 19 canonical residential functional zones, room orientations, elemental balance (Pancha Mahabhuta), directional harmony scoring, and non-structural remediation guidelines.

---

## 2. System Architecture & Technology Stack

The platform is engineered as a resilient, high-throughput microservices architecture:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT BROWSER (UI)                                  │
│             React 18 • Vite 5 • Responsive 2-Column Wide Workstation              │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │ HTTP / REST (:5173 / :8080)
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         NODE.JS API GATEWAY (Port 8080)                           │
│     Express 4 • Helmet (CSP/HSTS) • Rate Limiting • Reverse Proxy Middleware      │
└────────────────────────────────────────┬──────────────────────────────────────────┘
                                         │ Internal HTTP Proxy (:5000)
                                         ▼
┌───────────────────────────────────────────────────────────────────────────────────┐
│                       FLASK CORE ANALYSIS ENGINE (Port 5000)                      │
│                                                                                   │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌─────────────────────────┐  │
│  │   2D Drawing Reader   │ │  Effective Inputs &   │ │      SQLite DB        │  │
│  │  (RapidOCR + ONNX)    │ │   State Manager       │ │    (ACID Storage)     │  │
│  └──────────┬────────────┘ └──────────┬────────────┘ └────────────┬────────────┘  │
│             │                         │                           │               │
│             ▼                         ▼                           ▼               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                         THREE DOMAIN ENGINES                                │  │
│  │  1. Structure Engine (IS 456, IS 1893, NBC 2016 safety scoring)             │  │
│  │  2. Cost Engine (CPWD BOQ, Material/Labour fractions, GST)                  │  │
│  │  3. Vastu Engine (8-Direction Mandala, 19 Spatial Zones, Harmony Scoring)   │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Module Stack Breakdown

| Layer | Technology | Key Libraries / Modules | Responsibility |
| :--- | :--- | :--- | :--- |
| **Frontend** | React 18, Vite 5, JavaScript (ES2022) | `react-router-dom` v6, Vanilla CSS3 (Custom BEM Variables) | Interactive wide 2-column workstation, HMR, real-time input synchronization, responsive SVG plan canvas, tabbed BOQ viewer. |
| **API Gateway** | Node.js 18+, Express | `helmet`, `express-rate-limit`, `http-proxy-middleware`, `morgan` | Public edge ingress, security headers, request throttling, static asset streaming, proxy to Flask core. |
| **Backend Core** | Python 3.10+ / 3.12, Flask | `rapidocr-onnxruntime`, `numpy`, `Pillow`, `pypdf`, `sqlite3` | Plan ingestion, multi-angle OCR scanning, regex geometry heuristics, analysis orchestration, mathematical modeling. |
| **Database** | SQLite 3 | WAL mode, foreign keys enabled | Project records, plan binary metadata, cached OCR geometry trees, user manual overrides. |

---

## 3. Automated 2D Floor Plan Image Detection Pipeline

The drawing reader (`backend/app/plan_reader.py`) and parameter detector (`backend/app/detect.py`) extract structured building geometry from unstructured 2D architectural drawings without requiring manual annotation.

```
Uploaded Plan (PNG / JPG / PDF)
       │
       ▼
[Image Preprocessing] ──► Scale Pyramid (1.0x, 1.5x) + Rotation Quad (0°, 90°, -90°)
       │
       ▼
[ONNX RapidOCR] ────────► Bounding Box Detection + Confidence Scoring
       │
       ▼
[Coordinate Inversion] ──► Re-map rotated bounding boxes to original pixel space
       │
       ▼
[Token & Regex Parser] ──► Floor extraction ("GROUND", "1ST", "G+1")
                       ──► Dimension parsing ("15'0\" x 12'6\"" ──► inches ──► sq ft)
                       ──► Room classification (Fuzzy Levenshtein matching)
       │
       ▼
[Spatial 3x3 Grid] ────► Bounding box normalization into 9 Mandala cells
       │
       ▼
[Effective Inputs] ────► Merge detected fields with user manual overrides
```

### Step 1: Multi-Scale, Multi-Angle OCR Pyramid
Architectural plans frequently feature text rotated 90° along vertical wall lines (e.g., room dimensions, plumbing shafts). The reader processes the drawing across multiple views:
- **Scales**: Primary scale ($1.0\times$) and high-resolution upscaling ($1.5\times$ using Lanczos interpolation).
- **Rotations**:
  - $0^\circ$: Standard horizontal labels.
  - $+90^\circ$ (Counter-Clockwise): Left-aligned vertical walls.
  - $-90^\circ$ (Clockwise): Right-aligned vertical walls.

#### Coordinate Inversion Formulas
When OCR detects a bounding box $[x_0, x_1, y_0, y_1]$ in a rotated canvas of width $W'$ and height $H'$, coordinates are mapped back to original coordinates:
$$\text{Clockwise } (-90^\circ): \quad x = y', \quad y = W' - x'$$
$$\text{Counter-Clockwise } (+90^\circ): \quad x = H' - y', \quad y = x'$$

### Step 2: Dimension & Unit Parsing Engine
Dimensions are converted into exact inches via robust regular expressions:
$$\text{Regex: } \mathtt{\backslash d\{1,2\}\backslash s*['’`]\backslash s*(?:-?\backslash s*(\backslash d\{1,2\})\backslash s*(?:\"|”|''|’’)?)?}$$
- Example: `"15'6\""` $\rightarrow 15 \times 12 + 6 = 186\text{ inches}$.
- Area for room space:
  $$\text{Area (sq ft)} = \frac{W_{\text{inches}} \times D_{\text{inches}}}{144}$$

### Step 3: Room Classification Vocabulary
Extracted strings undergo fuzzy matching (Levenshtein ratio $>0.82$) against canonical room categories:
- **Kitchen**: `KITCHEN`, `KITCHN`, `MAINKITCHEN`, `COOKING`
- **Bedroom**: `BEDROOM`, `BEDRM`, `MBR`, `GUESTBED`, `KIDSBED`
- **Living**: `LIVINGROOM`, `LIVING`, `DRAWINGROOM`, `HALL`, `LOUNGE`
- **Dining**: `DINING`, `DININGROOM`, `DIN`
- **Toilet / Bath**: `TOILET`, `BATHROOM`, `WASHROOM`, `WC`, `POWDERROOM`
- **Balcony**: `BALCONY`, `TERRACE`, `DECK`, `VERANDAH`
- **Parking**: `PORTICO`, `PARKING`, `GARAGE`, `CARPORCH`
- **Pooja**: `POOJA`, `PUJA`, `MANDIR`, `PRAYER`
- **Stair**: `STAIRCASE`, `STAIR`, `LIFT`, `ELEVATOR`

### Step 4: 3×3 Mandala Spatial Matrix Mapping
The plan boundary is determined by the minimum bounding rectangle $[X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$ enclosing all detected rooms. The bounding box is divided into a $3 \times 3$ matrix:

$$\text{col} = \min\left(2, \left\lfloor \frac{x_{\text{center}} - X_{\min}}{(X_{\max} - X_{\min}) / 3} \right\rfloor\right)$$
$$\text{row} = \min\left(2, \left\lfloor \frac{y_{\text{center}} - Y_{\min}}{(Y_{\max} - Y_{\min}) / 3} \right\rfloor\right)$$
$$\text{Cell Index} = \text{row} \times 3 + \text{col} \quad (\in \{0, 1, 2, \dots, 8\})$$

#### Compass Zone Resolution
Given the user-confirmed orientation of North ($\text{North} \in \{\text{'top'}, \text{'right'}, \text{'bottom'}, \text{'left'}\}$):
$$\text{RING} = [0, 1, 2, 7, \text{None}, 3, 6, 5, 4]$$
$$\text{NORTH\_POS} = \{\text{'top'}: 1, \text{'right'}: 3, \text{'bottom'}: 5, \text{'left'}: 7\}$$
$$\text{Zone} = \text{COMPASS}[(\text{RING}[\text{Cell Index}] - \text{NORTH\_POS}[\text{north}]) \pmod 8]$$
Where $\text{COMPASS} = [\text{"N"}, \text{"NE"}, \text{"E"}, \text{"SE"}, \text{"S"}, \text{"SW"}, \text{"W"}, \text{"NW"}]$.

---

## 4. Analyzer 1: Structure Plan Analyzer

The Structure Analyzer evaluates 15 structural and architectural parameters, performs preliminary code compliance checks, and computes structural safety indices.

### The 15 Detected Specifications
1. **Building Type**: Residential Building (Villa / Independent House).
2. **Structure Type**: RCC Framed Structure / Load Bearing / Steel.
3. **Built-up Area**: Total floor footprint read directly from drawing dimensions.
4. **Plot Area**: Estimated site footprint using NBC 2016 standard ground coverage ($70\%$):
   $$\text{Plot Area} = \frac{\text{Built-up Area}}{0.70}$$
5. **Number of Floors**: Extracted level count ($G, G+1, G+2, \dots$).
6. **Total Building Height**: Calculated using $10\text{ ft}$ clear floor-to-floor height plus $3.5\text{ ft}$ plinth & parapet:
   $$H_{\text{ft}} = (\text{Floors} \times 10.0) + 3.5, \quad H_{\text{m}} = H_{\text{ft}} \times 0.3048$$
7. **Total Construction Area**:
   $$\text{Total Construction Area} = \text{Built-up Area} \times \text{Floors}$$
8. **Total Rooms**: Count of all distinct architectural enclosed spaces.
9. **Rooms per Floor**: Floor-wise inventory mapping space distributions.
10. **Number of Bedrooms**: Master, guest, and children's bedroom count.
11. **Number of Bathrooms**: Wet plumbing core and toilet counts.
12. **Number of Kitchens**: Main cooking zones and utility pantries.
13. **Number of Balconies**: Cantilevered slabs and portico areas.
14. **Concrete Grade**: Default M25 (or detected M20–M35) per IS 456 Table 2.
15. **Seismic Hazard Zone**: Zone II, III, IV, or V per IS 1893:2016 seismic zonation.

### Structural Safety Index Formulas
Safety scores are dynamically penalized based on seismic hazard, height/floors, and area:

$$\text{Floor Penalty } (P_{\text{fl}}) = \max(0, (\text{Floors} - 2) \times 3)$$
$$\text{Zone Penalty } (P_z) = \begin{cases} 0 & \text{Zone II} \\ 5 & \text{Zone III} \\ 10 & \text{Zone IV} \\ 15 & \text{Zone V} \end{cases}$$
$$\text{Area Penalty } (P_a) = \begin{cases} 5 & \text{if Built-up Area} > 3000\text{ sq ft} \\ 0 & \text{otherwise} \end{cases}$$

$$\mathbf{Load\text{ }Bearing\text{ }Capacity} = \max\left(55, \min\left(96, 92 - P_{\text{fl}} - \left\lfloor\frac{P_z}{2}\right\rfloor - P_a\right)\right)$$
$$\mathbf{Seismic\text{ }Resistance} = \max\left(50, \min\left(95, 90 - P_z - \left\lfloor\frac{P_{\text{fl}}}{2}\right\rfloor\right)\right)$$
$$\mathbf{Wind\text{ }Load\text{ }Stability} = \max\left(55, \min\left(96, 92 - \left\lfloor\frac{P_z}{2}\right\rfloor - \left\lfloor\frac{P_{\text{fl}}}{3}\right\rfloor\right)\right)$$
$$\mathbf{IS\text{ }456:2000\text{ }Index} = \max\left(50, \min\left(92, 85 - 2P_{\text{fl}} - \left\lfloor\frac{P_z}{3}\right\rfloor - P_a\right)\right)$$

### Code Standards Implemented
- **IS 456:2000**: Plain and Reinforced Concrete — Code of Practice.
  - Span-to-depth deflection limits (Clause 23.2): Basic $L/d = 20$ for simply supported beams, $7$ for cantilevers, $26$ for continuous spans.
  - Minimum column longitudinal steel (Clause 26.5.3.1): $0.8\%$ to $6.0\%$ of gross column cross-section.
- **IS 1893:2016 (Part 1)**: Earthquake Resistant Design of Structures.
  - Base shear evaluation: $V_b = A_h \times W$.
  - Ductile detailing requirements per **IS 13920:2016** for Zones III, IV, and V.
- **IS 875:1987 (Part 3)**: Design Loads (Wind Loads) on Buildings and Structures.

---

## 5. Analyzer 2: Cost Estimation Analyzer

The Cost Analyzer computes comprehensive financial forecasts, itemized quantities, and trade distributions calibrated against CPWD Schedule of Rates (DSR).

### Key Cost Formulas & Multipliers
- **Total Estimated Cost**:
  $$\text{Total Cost} = \text{Total Built-up Area (sq ft)} \times \text{Rate per sq ft (₹)}$$
  *(Default urban RCC benchmark rate: ₹1,950 / sq ft)*
- **AI Cost Range Prediction**:
  $$\text{Low Estimate} = 0.92 \times \text{Total Cost}$$
  $$\text{Most Likely} = 1.00 \times \text{Total Cost}$$
  $$\text{High Estimate} = 1.10 \times \text{Total Cost}$$
- **GST & Statutory Taxes (18% Construction Works Contract)**:
  $$\text{CGST } (9\%) = 0.09 \times \text{Total Cost}$$
  $$\text{SGST } (9\%) = 0.09 \times \text{Total Cost}$$
  $$\text{Total GST} = \text{CGST} + \text{SGST} = 0.18 \times \text{Total Cost}$$
  $$\text{Grand Total (All-in)} = 1.18 \times \text{Total Cost}$$

### Capital Allocation Fractions
- **Materials**: $58\%$ of base construction cost.
- **Labour Contracts**: $34\%$ of base construction cost.
- **Contractor Overheads & Margin**: $8\%$ of base construction cost.

### Material-wise Breakdown (58% of Total)
| Material Component | Share of Materials | Share of Total | Primary Function & Grade |
| :--- | :--- | :--- | :--- |
| **High-Yield TMT Steel** | $18\%$ | $10.4\%$ | Fe 550D rebar for columns, beams & slabs |
| **Cement** | $15\%$ | $8.7\%$ | OPC 53 & PPC for concrete, mortar & plaster |
| **Electrical & Plumbing** | $11\%$ | $6.4\%$ | CPVC pipes, copper wiring & conduit lines |
| **Sand & Aggregates** | $10\%$ | $5.8\%$ | M-Sand, plaster sand, 20mm/10mm gravel |
| **Tiles & Granite** | $9\%$ | $5.2\%$ | Vitrified floor tiles, granite kitchen slabs |
| **Bricks & AAC Blocks** | $8\%$ | $4.6\%$ | 200mm external & 100mm internal walls |
| **Doors & Windows** | $7\%$ | $4.1\%$ | Teak main door, UPVC sliding 3-track windows |
| **Paints & Emulsion** | $5\%$ | $2.9\%$ | Acrylic primer, putty & 2-coat weather coat |
| **Waterproofing** | $4\%$ | $2.3\%$ | Crystalline chemical screed for wet areas |
| **Hardware & Sundries** | $3\%$ | $1.7\%$ | Hinges, brass fixtures, anchors & sealants |

### Labour Trade Breakdown (34% of Total)
| Trade / Scope | Share of Labour | Share of Total | Trade Scope Description |
| :--- | :--- | :--- | :--- |
| **Formwork & Shuttering** | $30\%$ | $10.2\%$ | Plywood shuttering, steel props & staging |
| **Masonry & Plastering** | $25\%$ | $8.5\%$ | Brick laying, external & internal plastering |
| **Bar Bending & Tying** | $18\%$ | $6.1\%$ | Cutting, bending & binding rebar cages |
| **Electrical & Plumbing** | $12\%$ | $4.1\%$ | Conduit channelling, wiring & pipe laying |
| **Flooring & Stone Laying**| $9\%$ | $3.1\%$ | Tile fixing, grouting, edge chamfering |
| **Painting & Surface Prep**| $6\%$ | $2.0\%$ | Wall putty sanding, primer & roller paint |

### Itemized Bill of Quantities (BOQ) Coefficients per Sq Ft
$$\text{Calculated Quantity} = \text{Total Built-up Area} \times \text{BOQ Coefficient}$$

| Item # | Material / Work Description | Unit | Coefficient per Sq Ft | Standard Unit Rate (₹) |
| :---: | :--- | :---: | :---: | :---: |
| 1 | Cement (OPC 53 / PPC) | Bags | $0.42$ | ₹380 / bag |
| 2 | High-Yield TMT Steel (Fe 550D) | Metric Ton | $0.0038$ | ₹68,000 / MT |
| 3 | Manufactured Sand (M-Sand) | Cu. ft | $1.85$ | ₹65 / cu. ft |
| 4 | Coarse Aggregates (20mm & 10mm) | Cu. ft | $1.35$ | ₹48 / cu. ft |
| 5 | AAC Lightweight Wall Blocks | Nos | $2.60$ | ₹68 / block |
| 6 | Double-Charged Vitrified Tiles | Sq. ft | $0.85$ | ₹115 / sq. ft |
| 7 | Waterproofing Membrane | Sq. ft | $0.35$ | ₹45 / sq. ft |
| 8 | Acrylic Emulsion & Primer | Sq. ft | $3.20$ | ₹28 / sq. ft |
| 9 | Electrical Concealed Points | Points | $0.12$ | ₹850 / point |
| 10 | Plumbing Piping & Fittings | Running ft | $0.65$ | ₹145 / Rft |

---

## 6. Analyzer 3: Vastu Shastra AI Workstation

The Vastu Analyzer performs an 8-directional orientation check across 19 canonical functional zones, evaluating alignments against the principles of ancient Vedic architecture and environmental bio-energetics.

### The Five Elemental Energies (Pancha Mahabhuta)
```
             NORTH (Kubera / Mercury)
                   [Water / Jal]
                       │
       NW (Vayu)       │       NE (Ishan / Shiva)
       [Air / Vayu]    │       [Water & Ether]
             \         │         /
              \        │        /
               \       │       /
WEST ─────────── [Brahmasthan] ─────────── EAST (Indra / Sun)
(Varuna / Space) [Space / Akash]          [Fire & Light]
               /       │       \
              /        │        \
             /         │         \
       SW (Nairutya)   │       SE (Agni)
       [Earth / Prithvi]│      [Fire / Agni]
                       │
             SOUTH (Yama / Mars)
```

### 19 Canonical Spatial Zones Catalog
| Zone / Room | Ideal Orientation | Element & Governing Deity | Core Architectural Rationalization |
| :--- | :--- | :--- | :--- |
| **Master Bedroom** | Southwest (SW) | Earth (Prithvi) • Nairutya | Maximizes grounding, stability, and restful circadian cycles. Headboard should face South. |
| **Children's Bedroom** | West (W) / Northwest (NW) | Air (Vayu) • Varuna | Fosters academic focus, creative thinking, and restful development. |
| **Guest Bedroom** | Northwest (NW) | Air (Vayu) • Vayu | Ensures gracious hospitality while preserving homeowner authority in the core. |
| **Living Room** | North (N) / East (E) / NE | Water & Light • Ishan | Welcomes positive electromagnetic inflow and early morning solar radiation. |
| **Family Living Area** | North / East / Northeast | Ether & Light • Mitra | Fosters familial harmony, bonding, and open communication. |
| **Dressing Room** | West (W) / Southwest (SW) | Earth • Storage | Solid storage and wardrobes provide stability in heavy Southern/Western quadrants. |
| **Study Room** | East (E) / North (N) / NE | Water & Mercury • Brihaspati | Enhances intellectual stamina and memory. Desk positioned facing East. |
| **Home Office** | North (N) / East (E) | Water • Lord Kubera | Directs career and financial opportunities; desks positioned facing North/East. |
| **Main Kitchen** | Southeast (SE) | Fire (Agni) • Agni | Southeast corner governs metabolic energy and metabolic health. Cook faces East. |
| **Alternative Kitchen** | Northwest (NW) | Air • Vayu supporting Agni | Auxiliary culinary prep zone with exhaust ventilation in the Northwest quadrant. |
| **Dining Room** | East (E) / West (W) | Earth & Water • Aditi | Promotes healthy digestion and familial nourishment during meals. |
| **Pooja Room (Prayer)**| Northeast (NE) | Water & Ether • Ishanya | Highest vibrational sector; receives pure morning solar rays. Never place under stairs. |
| **Bathroom (Bath)** | West (W) / Northwest (NW) | Water • Varuna | Ensures optimal plumbing runoff without contaminating pure Northeast pranic inflows. |
| **Toilet (WC)** | West (W) / Northwest (NW) | Waste disposal • Vayu | Prevents toxic negative emanations from polluting living, prayer, or kitchen zones. |
| **Staircase** | South (S) / West (W) / SW | Heavy Earth • Nairutya | Heavy dead-load of concrete stairs belongs in South or West to anchor the structure. |
| **Main Gate / Entrance**| North (N) / East (E) | Solar Prana • Indra/Kuber | Auspicious primary threshold for positive life-force and financial flow. |
| **Garden / Lawn** | North (N) / East (E) | Vegetation & Light • Soma | Low-height landscaping keeps North/East light-well clear for sunlight penetration. |
| **Parking / Portico** | Northwest (NW) / SE | Mobility • Vayu | Mobile vehicle weights should be in transit quadrants; keep NE strictly unencumbered. |
| **Garage** | Northwest (NW) / SE | Mobility • Vayu | Enclosed parking spaces with fire separation away from Master and Pooja zones. |

### Vastu Harmony Scoring Algorithms
Each room placement is scored based on compass assignment:
- **Good (Ideal)**: $100\text{ points}$
- **Acceptable**: $65\text{ points}$
- **Avoid (Non-compliant)**: $15\text{ points}$
- **Unassigned / Unknown**: $50\text{ points}$

$$\mathbf{Overall\text{ }Harmony\text{ }Score\text{ }Index} = \frac{\sum_{i=1}^{N} w_i \times S_i}{\sum_{i=1}^{N} w_i}$$
*(Where critical zones like Kitchen, Master Bedroom, Pooja, and Toilet carry $w_i = 1.5$, while auxiliary spaces carry $w_i = 1.0$)*

#### Four Sub-KPI Scores:
1. **Entrance Analysis Score**: Evaluates main gate threshold alignment ($N/E = 90-100\%$, $NW/SE = 60-75\%$, $SW = 35\%$).
2. **Plot Suitability Score**: Evaluates rectangularity, cardinal aspect ratio, and slope.
3. **Direction-wise Score**: 8-direction radial bar chart ($0–100\%$) indicating energy distribution across compass quadrants.
4. **Room-wise Score**: Individual compliance card for each architectural space.

### Non-Structural Remediation Protocol
Every detected Vastu flaw generates a structured issue card containing:
- **Error**: Zone conflict explanation (e.g., Kitchen detected in Northeast).
- **Why It Matters**: Bio-energetic and functional consequence (e.g., Fire element in Water zone disturbs harmony).
- **Architectural Solution**: Plan-stage layout adjustment guidelines.
- **Traditional Remedy**: Non-structural physical cures (e.g., Copper Agni Yantra in Southeast, Lead helix in Southwest, Brass wind chimes in Northwest, pyramid paperweights).

---

## 7. Setup, Installation & Execution Guide

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.10, v3.11, or v3.12
- **npm**: v9.0.0 or higher

### 1. Automated Installation
Clone the repository and install all dependencies in one command:
```bash
git clone https://github.com/krishilvara005-bit/CivoraAI.git
cd CivoraAI

# Installs frontend, gateway, and backend packages
npm run install:all
```

### 2. Environment Configuration
Copy `.env.example` to create local configuration files:
```bash
cp .env.example .env
cp .env.example backend/.env
```
*(The platform runs 100% locally with on-device RapidOCR and does not require third-party paid API keys).*

### 3. Running in Development Mode
Start all three microservices concurrently:
```bash
npm run dev
```
Or on Windows, double-click:
```cmd
run_dev.bat
```

### Service Access URLs
| Service | Host URL | Description |
| :--- | :--- | :--- |
| **Frontend Application** | `http://localhost:5173` | React 18 UI with Vite Hot-Module Replacement |
| **API Gateway** | `http://localhost:8080` | Express Edge Gateway & Reverse Proxy |
| **Core Analysis Engine** | `http://127.0.0.1:5000` | Flask Python REST API & OCR Worker |

### 4. Production Build & Deployment
```bash
# Compile optimized React production bundle
npm run build

# Start production gateway serving the bundle
npm start
```

### 5. Running with Docker Compose
```bash
docker compose up --build
```
This boots the containerized multi-service platform at `http://localhost:8080`.

---

## 8. Automated Testing Suite

The backend contains a 25-point comprehensive automated verification suite checking API endpoints, validator bounds, drawing OCR parsing, structural safety calculations, and Vastu compliance algorithms.

To execute the test suite:
```bash
cd backend
python -m pytest tests -v
```

Expected output:
```
tests/test_api.py ..................                         [ 72%]
tests/test_engines.py .......                                [100%]
============================== 25 passed in 2.00s ==============================
```

---

## 9. Verification & Safety Disclaimer

*Civora AI provides automated preliminary decision-support modeling based on optical scanning and standard empirical codes. It does not replace certified structural engineering calculations, site geotechnical soil testing, or municipal sanction drawings. Always consult a licensed structural engineer and local municipal authorities before beginning physical construction.*
