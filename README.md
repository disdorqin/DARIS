<div align="center">

<img src="assets/banner.svg" width="100%" alt="DARIS Banner" />

</div>

## Autonomous Research Workflow OS

[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![License](https://img.shields.io/github/license/disdorqin/DARIS?style=flat-square&color=A3E635&logo=opensourceinitiative)](LICENSE)
[![Stars](https://img.shields.io/github/stars/disdorqin/DARIS?style=flat-square&color=00F5FF&logo=github)](https://github.com/disdorqin/DARIS/stargazers)
[![Status](https://img.shields.io/badge/STATUS-ACTIVE-00F5FF?style=flat-square&logo=circle&logoColor=white)](https://github.com/disdorqin/DARIS)
[![Forecasting](https://img.shields.io/badge/DOMAIN-Time%20Series%20Forecasting-A855F7?style=flat-square)](https://github.com/disdorqin/DARIS)

---

> DARIS (DAily Research & Intelligent System) is an autonomous research workflow operating system. It orchestrates multi-agent pipelines that go from raw research topic to publication-ready output — automating literature review, hypothesis generation, experiment execution, and knowledge asset production.

## Why DARIS Exists

Research is repetitive. Literature review, experiment tracking, hypothesis formatting — these are workflow problems, not intelligence problems. DARIS treats research as a programmable pipeline.

## Features

- **Config-Driven Orchestration** — YAML/JSON config defines the entire research workflow  
- **Multi-Agent System** — specializied agents for literature, hypothesis, experiment, and writing  
- **Literature Workflow** — automated arXiv/scholar ingestion, relevance scoring, summarization  
- **Experiment Monitor** — track forecasting experiments, NSE/MAE/R2 benchmarking  
- **Knowledge Asset Export** — auto-generate slides, reports, and draft papers  

## Architecture

<div align="center">
  <img src="assets/architecture.svg" width="100%" alt="Architecture" />
</div>

## Quick Start

```bash
# Clone and install
git clone https://github.com/disdorqin/DARIS.git
cd DARIS
npm install  # or: pnpm install

# Configure your research workflow
cp 1_config/example.json 1_config/config.json
# Edit config.json with your research topic and parameters

# Run the workflow
npm start
```

## Example Usage

```typescript
// Define a forecasting research workflow
const workflow = {
  topic: "electricity price forecasting with deep learning",
  hypothesis: "Transformer-based models outperform LSTM for short-term electricity price forecasting",
  experiment: {
    model: "Transformer",
    baseline: "LSTM",
    metrics: ["NSE", "MAE", "R2"],
    data: "electricity_price_dataset.csv"
  }
}

await daris.run(workflow)
// → Auto-ingests literature
// → Generates experiment design
// → Runs benchmarks
// → Produces draft report
```

## Roadmap

- [x] Multi-agent orchestration
- [x] Literature ingestion pipeline
- [ ] Hypothesis auto-generation with LLM
- [ ] Experiment auto-execution with tracking
- [ ] Draft paper generation
- [ ] Integration with tsplab for experiment management

## Tech Stack

TypeScript · Node.js · Python · OpenClaw · LLM APIs

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=disdorqin/DARIS&type=Date)](https://star-history.com/#disdorqin/DARIS&Date)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome.

## License

MIT — see [LICENSE](LICENSE).
