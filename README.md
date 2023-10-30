![ChimeraPy/aiodistbus](https://github.com/ChimeraPy/aiodistbus/assets/40870026/306bff08-612c-4cc2-8354-e2407a4c9de1)
<p align="center">
    <em>A Distributed Eventbus using ZeroMQ and AsyncIO for Python.</em>
</p>
<p align="center">
<a href="https://github.com/ChimeraPy/aiodistbus/actions?query=workflow%3ATest" target="_blank">
    <img src="https://github.com/ChimeraPy/aiodistbus/workflows/Test/badge.svg" alt="Test">
</a>

<a href='https://coveralls.io/github/ChimeraPy/aiodistbus?branch=main'>
    <img src='https://coveralls.io/repos/github/ChimeraPy/aiodistbus/badge.svg?branch=main' alt='Coverage Status' />
</a>
</p>

The objective of this library is to provide both a local and distributed eventbus that are compatible to communicate. A similar API can be used in both versions of the eventbuses implementations.

## Installation

For installing the package, download from PYPI and install with ``pip``:

```bash
pip install aiodistbus
```

## EventBus Example

TODO

## Design

In the ``aiodistbus`` library, we provided 2 eventbus implementations: ``EventBus`` and ``DEventBus``. The ``EventBus`` class is for local (within same Python runtime) observer pattern. In the other hand, ``DEventBus`` class is for a distributed eventbus that leverages ZeroMQ -- closing following the [Clone pattern](https://zguide.zeromq.org/docs/chapter5/).

The Clone pattern uses a client-server structure, where a centralized broker broadcasts messages sent by clients. As described in the ZeroMQ Guide, this creates a single point of failure, but yields in a simpler and more scalable implementation.

## Contributing
Contributions are welcomed! Our [Developer Documentation](https://chimerapy.readthedocs.io/en/latest/developer/index.html) should provide more details in how ChimeraPy works and what is in current development.

## License
[ChimeraPy](https://github.com/ChimeraPy) and [ChimeraPy/Orchestrator](https://github.com/ChimeraPy/Orchestrator) uses the GNU GENERAL PUBLIC LICENSE, as found in [LICENSE](./LICENSE) file.

## Funding Info
This project is supported by the [National Science Foundation](https://www.nsf.gov/) under AI Institute  Grant No. [DRL-2112635](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2112635&HistoricalAwards=false).
