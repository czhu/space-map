# Building and Maintaining the Documentation

Run these commands from the repository root using Python 3.10 or later:

```bash
pip install mkdocs mkdocs-material
mkdocs build --strict
mkdocs serve
```

Open `http://127.0.0.1:8000` for local preview. Static output is written to `site/`.
The current configuration uses the Material theme and Markdown extensions;
API pages are maintained as Markdown rather than generated from imports.
Building this documentation does not require running a registration experiment.

## Sources and navigation

`mkdocs.yml` controls navigation. The `docs/overview/` pages keep older repository
links usable and point to maintained guides. Scientific method descriptions live
in [Method and Scope](method.md); the [API reference](api/api.md) describes current
software behavior and implementation limitations.

When editing examples, check Python syntax, callable names and signatures,
coordinate/stage conventions, relative links, and the targets of current-branch
GitHub source links. A successful documentation build does not verify numerical
registration quality or reproduce a publication experiment.

## Deployment

`.github/workflows/docs.yml` is configured to build on pushes to `master`, releases,
and manual workflow dispatch, then publish files to the `gh-pages` branch.
The configured site target is `https://czhu.github.io/space-map`; successful build,
publish permissions, and repository Pages configuration are needed before that
address becomes usable. Check [Actions](https://github.com/czhu/space-map/actions)
for the actual result. Do not describe a configured deployment as a verified live site.

Until a site is available, readers can open the
[Markdown documentation on GitHub](https://github.com/czhu/space-map/tree/master/docs).
