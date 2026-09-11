<a name="readme-top"></a>

<style>
  .hero { text-align: center; font-family: Inter, sans-serif; }
  .badge-wall img { margin: 2px; }
</style>

<div class="hero" style="text-align:center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.png">
  </picture>
</div>

<center>
  <h1 class="hero" style="font-size:64px">✨ NEBULA QUEUE ✨</h1>
  <marquee behavior="scroll" direction="left">the last task queue you will ever need</marquee>
</center>

<div class="badge-wall" align="center">

[![tests](https://img.shields.io/github/actions/workflow/status/orbitlabs/nebula-queue/ci.yml?branch=main&style=for-the-badge)](https://github.com/orbitlabs/nebula-queue/actions)
[![PyPI](https://img.shields.io/pypi/v/nebula-queue?style=flat-square)](https://pypi.org/project/nebula-queue/)
[![downloads](https://img.shields.io/pypi/dm/nebula-queue?style=plastic)](https://pypi.org/project/nebula-queue/)
[![coverage](https://img.shields.io/codecov/c/github/orbitlabs/nebula-queue?style=for-the-badge)](https://codecov.io/gh/orbitlabs/nebula-queue)
[![license](https://img.shields.io/github/licence/orbitlabs/nebula-queue?style=flat)](LICENSE)
[![stars](https://img.shields.io/github/stars/orbitlabs/nebula-queue?style=social)](https://github.com/orbitlabs/nebula-queue/stargazers)
[![forks](https://img.shields.io/github/forks/orbitlabs/nebula-queue?style=social)](https://github.com/orbitlabs/nebula-queue/network/members)
[![issues](https://img.shields.io/github/issues/orbitlabs/nebula-queue?style=flat-square)](https://github.com/orbitlabs/nebula-queue/issues)
[![prs](https://img.shields.io/github/issues-pr/orbitlabs/nebula-queue?style=plastic)](https://github.com/orbitlabs/nebula-queue/pulls)
[![last commit](https://img.shields.io/github/last-commit/orbitlabs/nebula-queue?style=for-the-badge)](https://github.com/orbitlabs/nebula-queue/commits/main)
[![commit activity](https://img.shields.io/github/commit-activity/m/orbitlabs/nebula-queue?style=flat)](https://github.com/orbitlabs/nebula-queue/pulse)
[![contributors](https://img.shields.io/github/contributors/orbitlabs/nebula-queue?style=social)](https://github.com/orbitlabs/nebula-queue/graphs/contributors)
[![Discord](https://img.shields.io/discord/918273645?label=chat&logo=discord&style=for-the-badge)](https://discord.gg/nebulaq)
[![hits](https://hits.dwyl.com/orbitlabs/nebula-queue.svg)](https://hits.dwyl.com/orbitlabs/nebula-queue)
[![made with love](https://img.shields.io/badge/made%20with-%E2%9D%A4-red?style=for-the-badge)](https://github.com/orbitlabs)
[![python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)

</div>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com/?lines=Fast;Reliable;Distributed&center=true" alt="">
</p>

<video src="assets/demo.mp4" controls width="900"></video>

## 📖 Table of Contents

- [About](#about)
- [🚀 Quick Start](#quick-start)
- [📦 Installation](#installation)
- [⚙️ Configuration](#configuration)
- [🏗 Architecture](#architecture)
- [👥 Contributors](#contributors)
- [📈 Star History](#star-history)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## About

Nebula Queue is a distributed task queue for Python. It stores tasks in Redis
and runs them in worker processes. Tasks are retried with exponential backoff
and results are kept for a configurable time.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🚀 Quick Start

<details open>
<summary>Click to expand</summary>

```python
from nebula_queue import Broker

broker = Broker("redis://localhost:6379/0")

@broker.task
def resize(path):
    return path.upper()

resize.delay("cat.png")
```

</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📦 Installation

<details open>
<summary>Click to expand</summary>

```
pip install nebula-queue
```

</details>

See [the quickstart](docs/quickstart.md) and [the configuration reference](docs/configuration.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## ⚙️ Configuration

| Option | Default | Notes |
|---|---|---|
| `NEBULA_URL` | `redis://localhost:6379/0` | broker URL |
| `NEBULA_RESULT_TTL` | `3600` | seconds |
| `NEBULA_CONCURRENCY` | `8` | worker processes |
| `NEBULA_RETRY_MAX` | `5` | attempts |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🏗 Architecture

```mermaid
flowchart LR
  P[Producer] --> R[(Redis)]
  R --> W1[Worker 1]
  R --> W2[Worker 2]
  W1 --> S[(Results)]
  W2 --> S
```

<img src="assets/arch.png" alt="" loading="lazy" width="800">

See [the architecture notes](docs/architecture.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 👥 Contributors

<a href="https://github.com/orbitlabs/nebula-queue/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=orbitlabs/nebula-queue" loading="lazy">
</a>

<img src="https://github-readme-stats.vercel.app/api?username=orbitlabs&show_icons=true&theme=radical" alt="">

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=orbitlabs/nebula-queue&type=Date)](https://star-history.com/#orbitlabs/nebula-queue&Date)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
