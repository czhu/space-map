from __future__ import annotations
import space_map
import numpy as np
import pandas as pd
import os
import tifffile as tiff
import cv2

class FlowExport:
    def __init__(self, slices: list[space_map.Slice]):
        self.slices = slices
        self.ldmKey = "final_ldm"
        self.affineKey = "cell"
        self.initGridSlice = slices[0]
        self.initAffineSlice = slices[0]

    def export_affine_grid(self, affineShape=None, gridKey1="final_ldm", gridKey2="img", save=None):
        if affineShape is None:
            affineShape = space_map.img.get_shape()
        pack = {}
        pack["affine_shape"] = affineShape

        affines = []
        grids = []
        initS = self.initAffineSlice.index
        initI = 0
        for i, s in enumerate(self.slices):
            if s.index == self.initAffineSlice:
                initI = i
                affines.append(None)
                continue
            affine = s.data.loadH(initS, self.affineKey)
            affines.append(affine)
        i1 = (initI+1) % (len(self.slices) - 1)
        affines[initI] = np.zeros_like(affines[i1])
        
        for i, s in enumerate(self.slices):
            if s.index == self.initGridSlice:
                initI = i
                grids.append(None)
                continue
            grid = s.data.loadGrid(initS, gridKey1)
            if grid is None:
                grid = s.data.loadGrid(initS, gridKey2)
            grids.append(grid[0])
        i1 = (initI+1) % (len(self.slices) - 1)
        grids[initI] = np.zeros_like(grids[i1])
        
        a = np.array(affines)
        g = np.array(grids)
        pack["affines"] = a
        pack["grids"] = g
        if save:
            np.savez_compressed(save, **pack)
        return pack

    def write_tiffs(self, dfKey, key, prefix, center=False):
        imgs_ = self.export_imgs(dfKey, key, mchannel=False, he=False, scale=False, center=center)
        self.write_tiffs_imgs(imgs_, prefix)
    
    def export_imgs(self, dfKey, key, mchannel=True, he=False, scale=False, center=False):
        if center and dfKey == "DF":
            xys = np.concatenate([s.ps(key) for s in self.slices])
            mid = np.mean(xys, axis=0)
            xys = [np.array(s.ps(key)) - mid + space_map.XYRANGE / 2 for s in self.slices]
            imgs = [space_map.show_img(xy) for xy in xys]
        else:
            imgs = [s.get_img(dfKey, key, mchannel=mchannel, scale=scale, fixHe=he) for s in self.slices]
        return np.array(imgs)

    def export_dfs(self, keys_mapping, path=None):
        dfs = []
        for s in self.slices:
            index = s.index
            df = None
            for k, v in keys_mapping.items():
                ps = s.ps(k)
                if df is None:
                    df = pd.DataFrame(ps, columns=[v + "_x", v + "_y"])
                    df["index"] = index
                else:
                    df[v + "_x"] = ps[:, 0]
                    df[v + "_y"] = ps[:, 1]
            dfs.append(df)
        df = pd.concat(dfs, axis=0)
        if path is not None:
            df.to_csv(path, index=False)
        return df

    def _all_channel_keys(self):
        """Union of point-cloud channel keys across all slices (DF first)."""
        keys = []
        if any("DF" in s.imgs for s in self.slices):
            keys.append("DF")
        for s in self.slices:
            for k, img in s.imgs.items():
                if img.dfMode and k != "DF" and k not in keys:
                    keys.append(k)
        return keys

    def _channel_volume(self, ch, key, scale=True):
        """Rasterize one channel across all layers into a ``(Z, H, W)`` uint8
        volume; layers missing the channel become blank planes."""
        def render(sImg):
            img = space_map.show_img(sImg.get_points(key))
            if scale:
                n = int(space_map.XYRANGE / space_map.XYD)
                img = cv2.resize(img.astype(np.float32), (n, n))
            return img
        planes, shape = [], None
        for s in self.slices:
            if ch in s.imgs and s.imgs[ch].dfMode:
                p = render(s.imgs[ch]); shape = p.shape; planes.append(p)
            else:
                planes.append(None)
        if shape is None:
            return None
        planes = [pl if pl is not None else np.zeros(shape, np.float32)
                  for pl in planes]
        return (np.array(planes, np.float32) * 255).clip(0, 255).astype(np.uint8)

    def export_channel_tiffs(self, prefix, key=None, channels=None,
                             scale=True):
        """Write one 3D-volume TIFF per channel: shape ``(Z, H, W)``, Z = layers.

        Each aligned layer is rasterized to a density image; the layers are
        stacked along Z into a volume, and one ``<prefix>_<channel>.tiff`` is
        written per channel (density ``DF`` plus every cell-type / gene
        channel). A slice missing a channel contributes a blank plane so Z stays
        consistent across channels.

        key: which stored alignment to render (default ``align2``, the final
        non-rigid output). channels: restrict to these channel keys.
        """
        if key is None:
            key = space_map.Slice.align2Key
        keys = channels or self._all_channel_keys()
        dirr = os.path.dirname(prefix)
        if dirr and not os.path.exists(dirr):
            os.makedirs(dirr)
        written = []
        for ch in keys:
            vol = self._channel_volume(ch, key, scale)
            if vol is None:
                continue
            safe = ch.replace("::", "_").replace("/", "_")
            out = "%s_%s.tiff" % (prefix, safe)
            tiff.imwrite(out, vol)  # (Z, H, W)
            written.append(out)
            space_map.Info("Export channel volume %s -> %s %s" % (ch, out, vol.shape))
        return written

    def export_imaris_tiff(self, out_dir, key=None, channels=None,
                           size=1000, gain=32):
        """Write per-layer single-channel TIFFs for Imaris into ``out_dir``.

        Every layer is rasterized to a ``size x size`` density image (the render
        XYD is recomputed so XYRANGE maps onto ``size`` pixels), multiplied by
        ``gain`` (default 32) and clipped to 255 (uint8). Files are named:

            single channel : ``c_<layer>.tiff``
            multi channel   : ``c_<layer>_<channel>.tiff``

        ``<layer>`` is the slice id; ``<channel>`` is the channel key (``DF`` and
        every cell-type / gene channel, unless ``channels`` restricts the set).
        Returns the list of written paths.
        """
        if key is None:
            key = space_map.Slice.align2Key
        keys = list(channels or self._all_channel_keys())
        multi = len(keys) > 1
        os.makedirs(out_dir, exist_ok=True)

        # render XYD so XYRANGE spans exactly `size` pixels
        xyd = max(space_map.XYRANGE / size, 1e-9)

        def render(sImg):
            img = space_map.show_img(sImg.get_points(key), xyd=xyd)
            if img.shape[:2] != (size, size):
                img = cv2.resize(img.astype(np.float32), (size, size))
            img = (img.astype(np.float32) * gain).clip(0, 255).astype(np.uint8)
            return img

        written = []
        for s in self.slices:
            for ch in keys:
                if ch not in s.imgs or not s.imgs[ch].dfMode:
                    continue
                img = render(s.imgs[ch])
                if multi:
                    safe = ch.replace("::", "_").replace("/", "_")
                    fn = "c_%s_%s.tiff" % (s.index, safe)
                else:
                    fn = "c_%s.tiff" % s.index
                path = os.path.join(out_dir, fn)
                tiff.imwrite(path, img)  # (size, size) uint8
                written.append(path)
        space_map.Info("Export Imaris per-layer TIFFs -> %s (%d files, %dx%d)"
                       % (out_dir, len(written), size, size))
        return written

    def plot_3d(self, key=None, channel="DF", subsample=8000, z_gap=None,
                seed=0, save=None, title=None, by_celltype=None,
                elev=22, azim=45):
        """3D scatter of aligned layers stacked along Z, viewed at ~45 degrees.

        By default, if the slices carry cell-type channels (``ct::*``), points
        are colored by cell type (same type shares a color across layers) with a
        legend; otherwise each layer gets its own color. Set ``by_celltype`` to
        force either mode, or pass a specific ``channel`` to plot just that one.

        ``z_gap`` sets the spacing between layers (auto if None). Returns the
        Figure; set ``save`` to also write a PNG.
        """
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
        if key is None:
            key = space_map.Slice.align2Key
        rng = np.random.RandomState(seed)

        ct_keys = sorted({k for s in self.slices for k in s.imgs
                          if k.startswith("ct::")})
        if by_celltype is None:
            # auto-color by cell type only when no specific channel was asked for
            by_celltype = bool(ct_keys) and channel == "DF"

        def pts(sImg):
            a = np.asarray(sImg.get_points(key))
            if subsample and len(a) > subsample:
                a = a[rng.choice(len(a), subsample, replace=False)]
            return a

        # z spacing from the in-plane extent of the density channel
        spans = []
        for s in self.slices:
            if "DF" in s.imgs:
                a = np.asarray(s.imgs["DF"].get_points(key))
                if len(a):
                    spans.append(max(np.ptp(a[:, 0]), np.ptp(a[:, 1])))
        if z_gap is None:
            z_gap = (np.median(spans) / max(len(self.slices), 1)) if spans else 1.0

        fig = plt.figure(figsize=(9, 8))
        ax = fig.add_subplot(111, projection="3d")

        if by_celltype and ct_keys:
            cmap = plt.get_cmap("tab20")
            for ci, ch in enumerate(ct_keys):
                label = ch[len("ct::"):]
                color = cmap(ci % 20)
                first = True
                for i, s in enumerate(self.slices):
                    if ch not in s.imgs or not s.imgs[ch].dfMode:
                        continue
                    a = pts(s.imgs[ch])
                    if len(a) == 0:
                        continue
                    ax.scatter(a[:, 0], a[:, 1], np.full(len(a), i * z_gap),
                               s=0.4, alpha=0.5, color=color,
                               label=label if first else None)
                    first = False
            ax.legend(markerscale=12, loc="upper left", fontsize=8,
                      framealpha=0.9)
        else:
            cmap = plt.get_cmap("viridis")
            for i, s in enumerate(self.slices):
                if channel not in s.imgs or not s.imgs[channel].dfMode:
                    continue
                a = pts(s.imgs[channel])
                if len(a) == 0:
                    continue
                ax.scatter(a[:, 0], a[:, 1], np.full(len(a), i * z_gap),
                           s=0.3, alpha=0.4,
                           color=cmap(i / max(len(self.slices) - 1, 1)))

        ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("layer (Z)")
        ax.view_init(elev=elev, azim=azim)
        ax.set_title(title or ("3D reconstruction"
                               + (" by cell type" if by_celltype and ct_keys
                                  else " — %s" % channel)))
        fig.tight_layout()
        if save is not None:
            dirr = os.path.dirname(save)
            if dirr and not os.path.exists(dirr):
                os.makedirs(dirr)
            fig.savefig(save, dpi=150)
            space_map.Info("Export 3D plot -> %s" % save)
        return fig

    def export_all_channels(self, key, path=None):
        """Export every channel's aligned points for all slices as a long table.

        Columns: ``index`` (slice id), ``channel`` (imgKey, e.g. DF / ct::T /
        gene::CD3), ``x``, ``y``. Uses ``Slice.all_ps`` so density and every
        auxiliary channel are included.
        """
        rows = []
        for s in self.slices:
            for ch, ps in s.all_ps(key).items():
                sub = pd.DataFrame(ps, columns=["x", "y"])
                sub.insert(0, "channel", ch)
                sub.insert(0, "index", s.index)
                rows.append(sub)
        df = pd.concat(rows, axis=0, ignore_index=True)
        if path is not None:
            df.to_csv(path, index=False)
        return df

    def write_tiffs_imgs(self, imgs, prefix):
        imgs_ = imgs
        imgs_ *= 32
        imgs_[imgs_ > 255] = 255
        imgs_ = imgs_.astype(np.uint8)
        dirr = os.path.dirname(prefix)
        if not os.path.exists(dirr):
            os.makedirs(dirr)
        for i in range(imgs_.shape[0]):
            tiff.imwrite("%s_%d.tiff" % (prefix, i), imgs_[i])

    def write_tiffs_dfs(self, dfs, prefix):
        imgs = [space_map.show_img(df) for df in dfs ]
        self.write_tiffs_imgs(imgs, prefix)
    
    def import_imgs(self, key, imgs):
        for i, img in enumerate(imgs):
            if isinstance(img, str):
                img = cv2.imread(img)
            self.slices[i].save_value_img(img, key)
        