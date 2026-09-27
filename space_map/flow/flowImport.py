from __future__ import annotations
import numpy as np
import space_map
import json, os
import pandas as pd

class FlowImport:
    def __init__(self, basePath: str) -> None:
        self.slices = []
        self.basePath = basePath
        space_map.init_path(basePath)
        self.ratio = 1.4
        self.auto_init()

    @staticmethod
    def _target_size(size, ratio):
        """Round the padded extent up to a multiple of 1000, with a 1000 floor.

        Small extents (``size*ratio < 1000``) would otherwise floor to 0 and
        collapse XYRANGE; clamp to at least 1000 so small / test-scale inputs
        still get a valid canvas."""
        ts = (int(size * ratio / 1000)) * 1000
        return max(ts, 1000)

    def init_xys(self, xys: list[np.array], ids=None, norm=True) -> None:
        size = 0
        for i, s in enumerate(xys):
            sX, sY = s[:, 0], s[:, 1]
            sizeS = max(np.max(sX) - np.min(sX), np.max(sY) - np.min(sY))
            size = max(size, sizeS)
        xys2 = []
        targetSize = FlowImport._target_size(size, self.ratio)
        for i, s in enumerate(xys):
            # mid = np.mean(s, axis=0)
            if norm:
                mid = np.max(s, axis=0) / 2 + np.min(s, axis=0) / 2
                xys2.append(targetSize // 2 + s - mid)
            else:
                xys2.append(s)
        space_map.XYRANGE = targetSize
        xyd = int(targetSize / 400 / 5) * 5 + 5
        space_map.XYD = xyd
        space_map.Info(f"XYRANGE: {space_map.XYRANGE}, XYD: {space_map.XYD}")
        if ids is None:
            ids = [str(i) for i in range(len(xys))]
        
        self.slices = []
        dfs = []
        for i, s in enumerate(xys2):
            idd = ids[i]
            space_map.Info(f"Init Slice {idd} {s.shape}")
            slice = space_map.Slice(ids[i], self.basePath, i==0)
            df = pd.DataFrame(s, columns=["x", "y"])
            df["layer"] = i
            slice.init_df(df)
            dfs.append(df)
            slice.save_config()
            self.slices.append(slice)
        conf = {
            "XYD": space_map.XYD,
            "XYRANGE": space_map.XYRANGE,
            "ids": ids
        }
        dfs = pd.concat(dfs, axis=0, ignore_index=True)
        with open(self.basePath + "/conf.json", "w") as f:
            json.dump(conf, f)
        dfs.to_csv(self.basePath + "/raw/cells.csv.gz", index=False)
        return self.slices

    def _density_xy(self, layer):
        """Extract the density (N,2) coordinates from one multi-channel layer,
        whether the layer is a dict ({channel: array/df}) or a wide DataFrame."""
        if isinstance(layer, dict):
            d = np.asarray(layer["density"], dtype=np.float64)
            return d[:, :2]
        cols = list(layer.columns)
        xcol, ycol = ("x", "y") if ("x" in cols and "y" in cols) else (cols[0], cols[1])
        return layer[[xcol, ycol]].to_numpy(np.float64)

    def _shift_layer(self, layer, shift):
        """Return a copy of one multi-channel layer with x/y shifted by ``shift``.

        The SAME shift (derived from density) is applied to every channel so all
        channels of a slice stay in one coordinate frame."""
        if isinstance(layer, dict):
            out = {}
            for name, arr in layer.items():
                a = np.asarray(arr, dtype=np.float64).copy()
                a[:, 0] += shift[0]
                a[:, 1] += shift[1]
                out[name] = a
            return out
        df = layer.copy()
        cols = list(df.columns)
        xcol, ycol = ("x", "y") if ("x" in cols and "y" in cols) else (cols[0], cols[1])
        df[xcol] = df[xcol] + shift[0]
        df[ycol] = df[ycol] + shift[1]
        return df

    def init_multi(self, layers, ids=None, norm=True, celltype_col="celltype",
                   top_n=None):
        """Batch-import multi-channel layers (one per slice).

        ``layers`` is a list where each element is a multi-channel input for one
        slice — either a dict ``{channel: array}`` or a wide DataFrame (see
        ``Slice.init_df``). Coordinate normalization (extent -> XYRANGE/XYD, and
        the per-slice centering shift) is computed from each layer's DENSITY
        channel and applied identically to every channel, so channels never drift
        apart.
        """
        # Size / XYRANGE / XYD from density extents (same rule as init_xys).
        size = 0
        dens = [self._density_xy(l) for l in layers]
        for d in dens:
            sizeS = max(np.max(d[:, 0]) - np.min(d[:, 0]),
                        np.max(d[:, 1]) - np.min(d[:, 1]))
            size = max(size, sizeS)
        targetSize = FlowImport._target_size(size, self.ratio)
        space_map.XYRANGE = targetSize
        space_map.XYD = int(targetSize / 400 / 5) * 5 + 5
        space_map.Info(f"XYRANGE: {space_map.XYRANGE}, XYD: {space_map.XYD}")

        if ids is None:
            ids = [str(i) for i in range(len(layers))]

        self.slices = []
        for i, layer in enumerate(layers):
            if norm:
                d = dens[i]
                mid = np.max(d, axis=0) / 2 + np.min(d, axis=0) / 2
                shift = targetSize // 2 - mid
            else:
                shift = np.zeros(2)
            layer2 = self._shift_layer(layer, shift)
            slice = space_map.Slice(ids[i], self.basePath, i == 0)
            space_map.Info(f"Init Slice {ids[i]} (multi-channel)")
            slice.init_df(layer2, celltype_col=celltype_col, top_n=top_n)
            slice.save_config()
            self.slices.append(slice)

        conf = {"XYD": space_map.XYD, "XYRANGE": space_map.XYRANGE, "ids": ids}
        with open(self.basePath + "/conf.json", "w") as f:
            json.dump(conf, f)
        return self.slices

    def auto_init(self):
        path = self.basePath + "/conf.json"
        if os.path.exists(path):
            conf = json.load(open(path))
            space_map.XYRANGE = conf["XYRANGE"]
            space_map.XYD = conf["XYD"]
            space_map.Info(f"Auto Init: XYRANGE: {space_map.XYRANGE}, XYD: {space_map.XYD}")
            ids = conf["ids"]   
            self.slices = []
            for i, idd in enumerate(ids):
                slice = space_map.Slice(idd, self.basePath, i==0)
                self.slices.append(slice)
            return self.slices
        return []
    
    def init_from_codex(self, csvPath):
        df = pd.read_csv(csvPath)
        groups = df.groupby("array")
        pack = {}
        for g, dff in groups:
            xy = dff[["x", "y"]].values
            pack[g] = xy
        
        keys = list(pack.keys())
        keys.sort()
        keys2 = [(k, int(k[1:])) for k in keys]
        keys2.sort(key=lambda x: x[1])
        # print(keys2)
        xys = [pack[k[0]] for k in keys2]
        keys = [k[0] for k in keys2]
        # conf = {}
        # for i in range(len(xys)):
        #     conf[i] = keys[i]
        # with open(self.basePath + "/codex.json", "w") as f:
        #     json.dump(conf, f)
        space_map.Info(f"Init from codex: {keys}")
        return self.init_xys(xys, keys)

    def init_from_codex_multi(self, csvPath, layer_col="array",
                              celltype_col="celltype", extra_cols=None,
                              x_col="x", y_col="y", top_n=None):
        """Multi-channel serial-section import: keep celltype / gene columns.

        Groups rows by ``layer_col`` (one slice per group), and for each group
        builds a wide DataFrame ``[x, y, celltype?, *extra_cols]`` passed through
        the multi-channel ``init_multi``. Coordinate columns are renamed to
        ``x``/``y``. Layers are ordered ``S1..S10`` / numerically / then
        lexically. ``top_n`` caps the expanded cell types per slice.
        """
        df = pd.read_csv(csvPath)
        rename = {}
        if x_col != "x":
            rename[x_col] = "x"
        if y_col != "y":
            rename[y_col] = "y"
        if rename:
            df = df.rename(columns=rename)
        use = ["x", "y"]
        if celltype_col in df.columns:
            use.append(celltype_col)
        if extra_cols:
            use += [c for c in extra_cols if c in df.columns]

        groups = df.groupby(layer_col)
        pack = {g: dff[use].reset_index(drop=True) for g, dff in groups}

        def _order_key(k):
            # Sort S1,S2,...S10 numerically; plain ints/int-strings numerically;
            # everything else lexicographically.
            s = str(k)
            if len(s) > 1 and s[0].isalpha() and s[1:].isdigit():
                return (0, int(s[1:]))
            try:
                return (0, int(s))
            except ValueError:
                return (1, s)

        keys = sorted(pack.keys(), key=_order_key)
        layers = [pack[k] for k in keys]
        space_map.Info(f"Init from codex (multi): {keys}, cols={use}")
        return self.init_multi(layers, [str(k) for k in keys],
                               celltype_col=celltype_col, top_n=top_n)