# Architecture Diagram Guide

## Overview

This document describes the complete system architecture for the Crypto Quantitative Analytics Platform. Use this to create the architecture diagram in **draw.io**.

---

## System Architecture Diagram

### How to Create in draw.io

1. Go to https://app.diagrams.net/
2. Create new diagram
3. Use the components described below
4. Save as `architecture.drawio`
5. Export as PNG: `architecture.png`

---

## Component Layout (Top to Bottom)

```
┌──────────────────────────────────────────────────────────────────┐
│                        DATA SOURCE LAYER                          │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER                             │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                              │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                       ANALYTICS LAYER                             │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                         API LAYER                                 │
└──────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │  PRESENTATION LAYER  │    │    ALERT LAYER       │
        └──────────────────────┘    └──────────────────────┘
```

---

## Detailed Component Descriptions

### 1. DATA SOURCE LAYER

**Component:** Binance WebSocket API
- **Type:** Cloud/Rectangle
- **Color:** Light Blue
- **Icon:** Cloud or Database Server
- **Labels:**
  - "Binance WebSocket API"
  - "wss://stream.binance.com:9443"
  - "Real-time Tick Data"
- **Output:** Arrow labeled "Tick Stream (price, qty, timestamp)"

---

### 2. INGESTION LAYER

**Component:** WebSocket Client
- **Type:** Rectangle
- **Color:** Green
- **Icon:** Gear/Process
- **Labels:**
  - "WebSocket Ingestion Service"
  - "backend/ingestion/binance_websocket.py"
- **Functions:**
  - Async WebSocket client
  - Data validation
  - Reconnection logic
  - Error handling
- **Output:** Arrow labeled "Validated Tick Data"

---

### 3. STORAGE LAYER

Split into 3 sub-components:

#### 3a. Tick Repository
- **Type:** Rectangle
- **Color:** Orange
- **Labels:**
  - "Tick Data Repository"
  - "backend/storage/tick_repository.py"
- **Functions:**
  - Insert tick data
  - Query recent ticks
  - Time-range filters

#### 3b. OHLC Resampler
- **Type:** Rectangle (Process)
- **Color:** Purple
- **Labels:**
  - "OHLC Resampling Engine"
  - "backend/storage/ohlc_repository.py"
- **Functions:**
  - 1s, 1m, 5m resampling
  - VWAP calculation
  - Incremental updates

#### 3c. Database
- **Type:** Cylinder (Database shape)
- **Color:** Gray
- **Labels:**
  - "SQLite Database"
  - "crypto_analytics.db"
- **Tables:**
  - tick_data
  - ohlc_data
  - alert_rules
  - alert_history
  - analytics_cache

**Connections:**
- Tick Repository → Database (bidirectional)
- OHLC Resampler → Database (bidirectional)

---

### 4. ANALYTICS LAYER

Split into 2 sub-components:

#### 4a. Basic Statistics
- **Type:** Rectangle
- **Color:** Teal
- **Labels:**
  - "Basic Stats Calculator"
  - "backend/analytics/basic_stats.py"
- **Functions:**
  - Price statistics
  - Volume metrics
  - Volatility
  - VWAP

#### 4b. Pair Analytics
- **Type:** Rectangle
- **Color:** Teal
- **Labels:**
  - "Pair Trading Analyzer"
  - "backend/analytics/pairs_analytics.py"
- **Functions:**
  - Correlation (Pearson/Spearman)
  - Cointegration (ADF test)
  - Hedge ratio (OLS regression)
  - Spread calculation
  - Z-score analysis
  - Rolling metrics

**Input:** Arrows from OHLC Resampler
**Output:** Arrow labeled "Analytics Results"

---

### 5. API LAYER

**Component:** FastAPI REST API
- **Type:** Rectangle
- **Color:** Blue
- **Icon:** Server/API
- **Labels:**
  - "FastAPI REST API"
  - "backend/api/app.py"
  - "Port: 8000"
- **Endpoints (show as sub-boxes):**
  - `/api/health` - Health check
  - `/api/ticks/{symbol}` - Tick data
  - `/api/ohlc/{symbol}` - OHLC bars
  - `/api/stats/{symbol}` - Basic stats
  - `/api/pairs/analyze` - Pair analytics
  - `/api/symbols` - Symbol list
  - `/api/alerts/rules` - Alert CRUD
  - `/api/alerts/history` - Alert history
  - `/api/alerts/monitor/status` - Monitor status

**Input:** Arrows from Analytics components
**Output:** Arrow labeled "JSON/REST API"

---

### 6. PRESENTATION LAYER

**Component:** Streamlit Dashboard
- **Type:** Rectangle
- **Color:** Red/Pink
- **Icon:** Monitor/Display
- **Labels:**
  - "Streamlit Dashboard"
  - "frontend/dashboard.py"
  - "Port: 8501"
- **Pages (show as sub-boxes):**
  - Single Symbol Analysis
  - Pair Trading Analysis
  - Multi-Symbol Dashboard
- **Features:**
  - Interactive Plotly charts
  - Real-time updates
  - User controls
  - Auto-refresh

**Input:** Arrow from API Layer (HTTP/REST)
**Output:** Arrow to "User Browser"

---

### 7. ALERT LAYER

Split into 4 sub-components (all in same layer):

#### 7a. Alert Manager
- **Type:** Rectangle
- **Color:** Yellow
- **Labels:**
  - "Alert Manager"
  - "backend/alerts/alert_manager.py"
- **Functions:**
  - Check alert rules
  - Calculate Z-scores
  - Trigger detection
  - Cooldown management

#### 7b. Alert Storage
- **Type:** Rectangle
- **Color:** Yellow
- **Labels:**
  - "Alert Storage"
  - "backend/alerts/alert_storage.py"
- **Functions:**
  - Rule persistence
  - History tracking
  - CRUD operations

#### 7c. Notification Service
- **Type:** Rectangle
- **Color:** Yellow
- **Labels:**
  - "Notification Service"
  - "backend/alerts/notification_service.py"
- **Channels:**
  - Webhooks (HTTP POST)
  - Email (SMTP)
  - Telegram (Bot API)

#### 7d. Background Monitor
- **Type:** Rectangle (Process with clock icon)
- **Color:** Yellow
- **Labels:**
  - "Background Monitor"
  - "backend/alerts/monitor.py"
  - "Check Interval: 60s"
- **Functions:**
  - Continuous monitoring
  - Scheduled checks
  - Thread management

**Connections:**
- Alert Manager ↔ Alert Storage
- Alert Manager → Notification Service
- Background Monitor → Alert Manager (triggers checks)
- Alert Storage → Database
- Notification Service → External Services (webhooks, email servers)

**Input:** Arrow from API Layer (data)
**Output:** Arrows to "Webhook Endpoints", "Email Servers", "Telegram API"

---

## Data Flow Arrows

### Primary Data Flow (Real-time Path)
```
Binance WebSocket
    ↓ (tick stream)
WebSocket Ingestion
    ↓ (validated ticks)
Tick Repository
    ↓ (store)
Database
    ↓ (read ticks)
OHLC Resampler
    ↓ (OHLC bars)
Database
    ↓ (read bars)
Analytics Engine
    ↓ (analytics results)
API Layer
    ↓ (JSON/REST)
Dashboard
```

### Alert Flow (Background Path)
```
Database
    ↓ (OHLC data)
Alert Manager
    ↓ (check rules)
[If triggered]
    ↓
Notification Service
    ↓ (send alerts)
External Services (Webhook/Email/Telegram)
```

---

## Color Coding Guide

- **Light Blue**: External data sources
- **Green**: Data ingestion
- **Orange**: Data storage/repositories
- **Purple**: Data processing/transformation
- **Gray**: Database
- **Teal**: Analytics/computation
- **Blue**: API/services
- **Red/Pink**: User interface
- **Yellow**: Alert system

---

## Key Features to Highlight

### Modularity
- Each layer is independent
- Loose coupling via interfaces
- Can swap SQLite → PostgreSQL
- Can add new data sources easily

### Scalability Points
- Horizontal scaling: Multiple WebSocket clients
- Caching layer: Add Redis between Analytics and API
- Load balancing: Multiple API instances
- Message queue: Add Kafka/RabbitMQ for ingestion

### Real-time Processing
- WebSocket → Sub-second latency
- OHLC resampling → Incremental updates
- Alert monitoring → 60-second checks
- Dashboard refresh → 5-10 second updates

---

## Labels for draw.io

### Title
"Crypto Quantitative Analytics Platform - System Architecture"

### Legend Box
Create a legend showing:
- Rectangle = Component/Service
- Cylinder = Database
- Cloud = External API
- Arrows = Data flow direction
- Dotted lines = Async/background processes

### Technology Stack Annotation
Add a text box listing:
- Backend: Python 3.9+, FastAPI, SQLAlchemy
- Frontend: Streamlit, Plotly
- Database: SQLite (production: PostgreSQL/TimescaleDB)
- WebSocket: websockets library
- Analytics: Pandas, NumPy, Statsmodels
- Notifications: SMTP, Telegram Bot API, HTTP webhooks

---

## Export Instructions

1. **Save as .drawio**
   - File → Save As → `architecture.drawio`
   - Include in project root

2. **Export as PNG**
   - File → Export As → PNG
   - Resolution: 300 DPI minimum
   - Transparent background: No
   - Border width: 10px
   - Save as: `architecture.png`

3. **Export as SVG** (optional)
   - File → Export As → SVG
   - Include copy of source: Yes
   - Save as: `architecture.svg`

---

## Alternative: ASCII Art Diagram (if needed)

```
                                    ┌─────────────────────┐
                                    │  Binance WebSocket  │
                                    │   (External API)    │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ WebSocket Ingestion │
                                    │     (AsyncIO)       │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                        ┌──────────────────────┴────────────────────┐
                        │                                            │
                        ▼                                            ▼
            ┌─────────────────────┐                     ┌─────────────────────┐
            │  Tick Repository    │────────────────────▶│   OHLC Resampler    │
            │   (DAO Pattern)     │                     │  (1s, 1m, 5m bars)  │
            └──────────┬──────────┘                     └──────────┬──────────┘
                       │                                            │
                       └──────────────────┬─────────────────────────┘
                                          │
                                          ▼
                                ┌──────────────────────┐
                                │  SQLite Database     │
                                │  - tick_data         │
                                │  - ohlc_data         │
                                │  - alert_rules       │
                                │  - alert_history     │
                                └──────────┬───────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        │                                      │
                        ▼                                      ▼
            ┌─────────────────────┐              ┌─────────────────────┐
            │  Basic Stats        │              │  Pair Analytics     │
            │  - Price stats      │              │  - Correlation      │
            │  - Volume metrics   │              │  - Cointegration    │
            │  - Volatility       │              │  - Hedge ratio      │
            └──────────┬──────────┘              │  - Z-score          │
                       │                         └──────────┬──────────┘
                       └──────────────┬──────────────────────┘
                                      │
                                      ▼
                           ┌────────────────────────┐
                           │   FastAPI REST API     │
                           │   - /api/health        │
                           │   - /api/ticks         │
                           │   - /api/ohlc          │
                           │   - /api/stats         │
                           │   - /api/pairs/analyze │
                           │   - /api/alerts/*      │
                           └──────────┬─────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
        ┌───────────────────────┐         ┌───────────────────────┐
        │  Streamlit Dashboard  │         │    Alert System       │
        │  - Single Symbol      │         │  ┌─────────────────┐  │
        │  - Pair Trading       │         │  │ Alert Manager   │  │
        │  - Multi-Symbol       │         │  │ Rule Checker    │  │
        │  - Auto-refresh       │         │  └────────┬────────┘  │
        └───────────────────────┘         │           │           │
                                          │  ┌────────▼────────┐  │
                                          │  │ Notification    │  │
                                          │  │ Service         │  │
                                          │  │ - Webhooks      │  │
                                          │  │ - Email         │  │
                                          │  │ - Telegram      │  │
                                          │  └─────────────────┘  │
                                          └───────────────────────┘
```

---

## Summary

This architecture demonstrates:

✅ **Clean separation of concerns** - Each layer has one responsibility
✅ **Loose coupling** - Components communicate via interfaces
✅ **Extensibility** - Easy to add new data sources, analytics, or notifications
✅ **Scalability** - Clear scaling paths identified
✅ **Real-time processing** - WebSocket → Storage → Analytics → UI pipeline
✅ **Production-ready patterns** - Repository pattern, service layer, API gateway

Use this document to create a professional architecture diagram in draw.io that clearly shows the evaluator your system design thinking.
