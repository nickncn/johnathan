# 🏛️ Johnathan- AI-Driven Risk Dashboard

**Professional portfolio risk management platform with real-time monitoring and AI-powered insights**

<div align="center">

[![CI/CD Pipeline](https://github.com/nickncn/johnathan/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/nickncn/johnathan/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

[🚀 Quick Start](#-quick-start) • [📊 Features](#-features) • [🏗️ Architecture](#%EF%B8%8F-architecture) • [📖 Documentation](#-documentation) • [🤝 Contributing](#-contributing)

![Risk Dashboard Preview](https://via.placeholder.com/800x400/1f2937/ffffff?text=Risk+Dashboard+Screenshot)

</div>

---

## 🎯 **What is Johnathan?**

Johnathan is a **production-ready, institutional-grade** portfolio risk management platform that combines real-time financial analytics with AI-powered insights. Built for trading desks, hedge funds, and crypto funds who need professional risk monitoring with natural language explanations.

### **Think Bloomberg Terminal + ChatGPT for Risk Management**

- 📈 **Real-Time Monitoring**: Live P&L, VaR calculations, position tracking
- 🤖 **AI Risk Analysis**: "Explain why VaR jumped 30% today" with actionable insights  
- 📊 **Professional Analytics**: Multiple VaR models, exposure analysis, concentration risk
- ⚡ **Live Streaming**: WebSocket feeds for prices, alerts, and portfolio updates
- 🏛️ **Enterprise Ready**: Docker deployment, comprehensive testing, audit trails

---

## 🚀 **Quick Start**

### **One-Command Setup**
```bash
# Clone and start everything
git clone https://github.com/nickncn/johnathan.git
cd johnathan
cp .env.example .env
docker compose up --build

# In another terminal: seed with 180 days of sample data
docker compose exec api python scripts/seed_data.py

# Access the platform
open http://localhost:3000  # 📊 Dashboard  
open http://localhost:8000/docs  # 📚 API Docs
```

### **What You'll See**
- **Dashboard** (`/dashboard`) - Portfolio overview with live KPIs and charts
- **Positions** (`/positions`) - Real-time position table with P&L breakdown  
- **Risk Analysis** (`/risk`) - VaR calculations and exposure analytics
- **AI Reports** (`/reports`) - Generate intelligent risk summaries

---

## 📊 **Features**

<table>
<tr>
<td width="50%">

### **🔴 Real-Time Risk Engine**
- **Value at Risk (VaR)**
  - Historical Simulation 
  - Parametric (Normal)
  - EWMA Volatility
- **Live P&L Tracking**
  - Unrealized/Realized P&L
  - Position-level attribution
  - Portfolio-level aggregation
- **Risk Alerts** 
  - Threshold-based notifications
  - Real-time WebSocket delivery

</td>
<td width="50%">

### **🤖 AI-Powered Insights**
- **Natural Language Summaries**
  - Risk metric explanations
  - Position impact analysis
  - Trend identification
- **Automated Reports**
  - Daily risk memos
  - Key driver identification  
  - Actionable recommendations
- **Multi-LLM Support**
  - OpenAI GPT-4
  - Anthropic Claude

</td>
</tr>
<tr>
<td width="50%">

### **📈 Professional Analytics** 
- **Exposure Analysis**
  - Asset class breakdown
  - Currency exposure
  - Sector concentration
- **Portfolio Metrics**
  - Sharpe ratio calculation
  - Maximum drawdown
  - Correlation analysis
- **Multi-Asset Support**
  - Equities, Crypto, FX
  - Options (planned)

</td>
<td width="50%">

### **⚡ Production Features**
- **Real-Time Streaming**
  - Live price feeds (2s updates)
  - P&L updates (10s intervals)
  - Instant risk alerts
- **Enterprise Architecture**
  - Docker containerization
  - Horizontal scaling ready
  - Comprehensive monitoring
- **Security & Compliance**
  - JWT authentication
  - Audit logging
  - Input validation

</td>
</tr>
</table>

---

## 🏗️ **Architecture**

```mermaid
graph TB
    subgraph "Frontend Layer"
        WEB[Next.js Dashboard<br/>TypeScript + Tailwind]
        CHART[Recharts Visualizations]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend<br/>Python + Async]
        WS[WebSocket Streaming]
    end
    
    subgraph "Business Logic"
        PNL[P&L Service]
        VAR[VaR Calculations]
        AI[LLM Integration]
        EXP[Exposure Analysis]
    end
    
    subgraph "Data Layer"  
        DB[(PostgreSQL<br/>Time-series optimized)]
        REDIS[(Redis<br/>Cache + Pub/Sub)]
    end
    
    subgraph "Background"
        CELERY[Celery Workers]
        TASKS[Data Ingestion<br/>Risk Calculations]
    end
    
    WEB --> API
    WEB -.-> WS
    API --> PNL
    API --> VAR
    API --> AI
    API --> EXP
    PNL --> DB
    VAR --> DB
    WS --> REDIS
    CELERY --> TASKS
    TASKS --> DB
```

### **Technology Stack**

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Async/Await |
| **Database** | PostgreSQL 15, Redis 7 |
| **Computing** | NumPy, Pandas, SciPy for financial calculations |
| **AI/ML** | OpenAI GPT-4, Anthropic Claude |
| **Infrastructure** | Docker, Celery, WebSockets |
| **Testing** | Pytest, Jest, Hypothesis (property-based testing) |

---

## 📖 **Documentation**

### **📚 Core Guides**
- [🚀 **Quick Start Guide**](docs/quick-start.md) - Get running in 5 minutes
- [🏗️ **Architecture Overview**](docs/architecture.md) - System design and components
- [🔧 **Development Setup**](docs/development.md) - Local development environment
- [🚢 **Deployment Guide**](docs/deployment.md) - Production deployment

### **📊 Risk Management**
- [📈 **VaR Calculations**](docs/var-calculations.md) - Mathematical methodology
- [💰 **P&L Tracking**](docs/pnl-tracking.md) - Position and portfolio P&L
- [⚖️ **Risk Metrics**](docs/risk-metrics.md) - All supported risk measures
- [🤖 **AI Integration**](docs/ai-integration.md) - LLM setup and configuration

### **🔌 API Reference**
- [📋 **REST API**](http://localhost:8000/docs) - Interactive API documentation
- [⚡ **WebSocket API**](docs/websocket-api.md) - Real-time data feeds
- [🔐 **Authentication**](docs/authentication.md) - JWT tokens and security

---

## 💼 **Use Cases**

<table>
<tr>
<td width="33%">

### **🏦 Portfolio Managers**
- Monitor real-time P&L across all positions
- Get AI explanations for portfolio changes
- Generate daily risk reports for stakeholders
- Set custom risk thresholds and alerts

</td>
<td width="33%">

### **⚖️ Risk Officers**
- Calculate regulatory VaR measures
- Monitor concentration limits and exposures  
- Validate risk calculations independently
- Ensure compliance with risk mandates

</td>
<td width="33%">

### **🔬 Quantitative Analysts**
- Access granular risk calculation data
- Integrate with existing risk systems
- Validate financial models and assumptions
- Customize VaR parameters and methodologies

</td>
</tr>
</table>

---

## 🚦 **Getting Started**

### **Prerequisites**
- **Docker** & Docker Compose (recommended)
- **OR** Python 3.11+ and Node.js 18+ for manual setup

### **🐳 Docker Setup (Recommended)**
```bash
# 1. Clone repository
git clone https://github.com/nickncn/johnathan.git
cd johnathan

# 2. Configure environment  
cp .env.example .env
# Edit .env with your LLM API keys (optional for demo)

# 3. Start all services
docker compose up --build

# 4. Seed with sample data (in new terminal)
docker compose exec api python scripts/seed_data.py

# 5. Access the platform
open http://localhost:3000
```

### **🔧 Manual Development Setup**

<details>
<summary>Click to expand manual setup instructions</summary>

**Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .[dev]

# Setup database
createdb risk_dashboard
alembic upgrade head
python scripts/seed_data.py

# Start API server
uvicorn app.main:app --reload
```

**Frontend Setup**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

**Background Services**
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker  
cd backend
celery -A app.workers.tasks worker --loglevel=info

# Terminal 3: Celery Beat
celery -A app.workers.tasks beat --loglevel=info
```

</details>

---

## 🎮 **Usage Examples**

### **📊 Dashboard Monitoring**
The main dashboard provides real-time portfolio overview:
- **KPI Cards**: Total P&L, VaR, Portfolio Value
- **Live Charts**: P&L history, price tickers
- **Position Table**: Top positions with contribution analysis
- **Real-Time Updates**: WebSocket-driven live data

### **⚡ WebSocket Integration**
```javascript
const ws = new WebSocket('ws://localhost:8000/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'pnl_update') {
    updatePortfolioDisplay(data.data);
  } else if (data.type === 'risk_alert') {
    showRiskAlert(data.data.message, data.data.severity);
  }
};
```

### **🔌 API Usage**
```bash
# Get JWT token (demo)
export TOKEN="your-jwt-token"

# Current portfolio P&L
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/pnl/summary

# Calculate 99% Historical VaR
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8000/api/risk/var?alpha=0.99&method=historical"

# Generate AI risk summary
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"alpha": 0.99, "lookback_days": 250}' \
     http://localhost:8000/api/llm/summary
```

### **🤖 AI Risk Analysis**
Generate intelligent risk summaries:
```python
# Example AI-generated risk summary
"""
📊 PORTFOLIO RISK ANALYSIS - 99% VaR: $1.2M

KEY FINDINGS:
• VaR increased 15% vs last week due to increased crypto allocation
• Tesla position (18% of portfolio) drives 60% of portfolio volatility  
• Currency exposure: 85% USD, 15% EUR creates modest FX risk
• Correlation between tech stocks elevated at 0.78 (vs historical 0.45)

RISK DRIVERS:
• TSLA volatility spike following earnings announcement
• Crypto market correlation breakdown affecting diversification
• Tech sector concentration above 40% threshold

RECOMMENDATIONS:
• Consider reducing TSLA position to <15% of portfolio
• Add defensive positions to offset tech concentration
"""
```

---

## 📈 **Sample Data & Demo**

The platform includes realistic sample data:
- **10 instruments** - Mix of equities (AAPL, GOOGL, TSLA), crypto (BTC, ETH), and FX
- **180 days** of price history with realistic volatility patterns
- **50-100 trades** generating current portfolio positions
- **Live simulated feeds** - Price updates every 2 seconds, P&L every 10 seconds

### **Demo Scenarios**
- Portfolio value: ~$500,000
- Current P&L: $12,345 (2.47% return)
- 99% VaR: ~$45,000 (9% of portfolio)
- Positions across 8 instruments with realistic concentration

---

## 🧪 **Testing & Quality**

### **🔬 Comprehensive Test Suite**
- **Backend**: 90%+ test coverage with pytest
  - Unit tests for all financial calculations
  - Integration tests for API endpoints  
  - Property-based tests using Hypothesis
  - Performance tests for risk calculations

- **Frontend**: Component and integration testing
  - Jest + React Testing Library
  - E2E tests for critical user flows
  - Visual regression testing

### **📊 Financial Model Validation**
- VaR calculations validated against academic benchmarks
- P&L reconciliation with manual calculations
- Edge case testing (zero positions, extreme values)
- Property-based testing for mathematical invariants

### **🔍 Code Quality**
```bash
# Run all tests
make test

# Code quality checks
make lint

# Security scanning  
make security-scan
```

---

## 🚀 **Deployment**

### **🐳 Production Docker**
```bash
# Production deployment
docker compose -f deploy/docker/docker-compose.prod.yml up -d

# Health check
curl http://localhost:8000/health
```

### **☁️ Cloud Deployment**
The platform is ready for cloud deployment on:
- **AWS**: ECS, RDS, ElastiCache
- **Google Cloud**: Cloud Run, Cloud SQL, Memorystore
- **Azure**: Container Instances, PostgreSQL, Redis Cache

### **🔧 Configuration**
Key environment variables:
```bash
# Database & Cache
DATABASE_URL=postgresql://user:pass@host:5432/risk_dashboard
REDIS_URL=redis://host:6379/0

# Security
JWT_SECRET=your-production-secret-key

# AI Integration
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-api-key

# Risk Parameters
DEFAULT_VAR_ALPHA=0.99
VAR_ALERT_THRESHOLD=1000000
```

---

## 🤝 **Contributing**

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### **🎯 High-Priority Areas**
- [ ] Additional VaR methods (Monte Carlo, Extreme Value Theory)
- [ ] Options and derivatives support
- [ ] Enhanced AI explanations and insights
- [ ] Mobile-responsive improvements
- [ ] Advanced visualization components

### **🛠️ Development Process**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow our code style guidelines (Black, ESLint, TypeScript)
4. Add tests for new functionality
5. Ensure all tests pass: `make test`
6. Submit a pull request

### **👥 Community**
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/nickncn/johnathan/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/nickncn/johnathan/discussions)
- 📖 **Documentation**: Help improve our docs and guides

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Financial Mathematics**: Based on established risk management literature
- **Open Source**: Built with amazing open-source technologies
- **Community**: Thanks to all contributors and users

---

<div align="center">

**Built with ❤️ for the financial technology community**

[⭐ Star this repo](https://github.com/nickncn/johnathan) • [🐛 Report Bug](https://github.com/nickncn/johnathan/issues) • [💡 Request Feature](https://github.com/nickncn/johnathan/discussions)

</div>
