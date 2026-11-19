# Installation and Configuration

Use Python 3.10 or later. The repository's CI tests Python 3.10–3.12 on Linux
and macOS; this is not a claim that every backend or platform has been tested.

## Install from source

```bash
git clone https://github.com/czhu/space-map.git
cd space-map
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

`setup.py` installs the dependencies listed in `requirement.txt`. Direct
installation without cloning is also possible:

```bash
pip install git+https://github.com/czhu/space-map.git
```

Clone the repository when using its notebooks and example files. The package
name used by pip is `space-map`; the Python import name is `space_map`.

## Verify the installation

```bash
python -c "import space_map; print(space_map.__version__)"
space-map register --help
```

## Configure a run

For a notebook, set the local data path and coordinate/section column names in
its first code cell. The gene-expression notebook also needs a matrix directory
per section and matching cell identifiers. See [Examples](../examples/examples.md).

For Python, use `RegistrationConfig(workdir=..., seed=...)` as shown in the
[quick start](quickstart.md). Use a distinct working directory per dataset and
configuration. The public wrapper recomputes input normalization on import;
legacy low-level globals are not substitutes for an explicit run configuration.

## Matcher and hardware

The default `auto` matcher includes Kornia LoFTR and downloads its pretrained
checkpoint on first use. Set `--method sift_vgg` for a SIFT-only matcher that
does not require that download. The historical `sift_vgg` name does not load a
VGG network in the current SIFT helper.

CPU execution is supported. CUDA acceleration needs a compatible PyTorch build;
use the [PyTorch installation selector](https://pytorch.org/get-started/locally/)
for the appropriate platform instructions. Device detection and stage-specific
backend selection are not identical; see [LDDMM implementation notes](../registration/registration-system-(lddmm).md#devices-and-resource-use).
The paper's laptop measurements are specific to its datasets and settings,
not a minimum-memory specification for every possible stack.

## Troubleshooting and updates

If `import space_map` fails, confirm that the active Python environment contains
the package and its dependencies. To update an editable source installation:

```bash
git pull origin master
pip install -e .
```

For an alignment or backend failure, report the package/Python versions,
configuration, relevant logs, and a minimal reproducible input through
[GitHub Issues](https://github.com/czhu/space-map/issues).
