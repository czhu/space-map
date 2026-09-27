import space_map
import os
import pandas as pd
import matplotlib.pyplot as plt
import cv2, json
import numpy as np
from . import SliceData

class SliceImg:
    DF = "DF"
    Img = "IMG"
    def __init__(self, index, imgKey, dfMode=False,
                 heMode=False, projectf=None, role=None, nPoints=0):
        self.index = str(index)
        self.projectf = space_map.BASE if projectf is None else projectf
        self.imgKey = imgKey
        self.dfMode = dfMode
        self.heMode = heMode
        # role: which kind of channel this is ("density"/"celltype"/"gene"/None).
        # nPoints: product count (cells / expression points) used to weight this
        # channel when scoring candidate affine matrices.
        self.role = role
        self.nPoints = int(nPoints)

    def to_config(self):
        return {
            "index": self.index,
            "key": self.imgKey,
            "dfMode": "TRUE" if self.dfMode else "FALSE",
            "heMode": "TRUE" if self.heMode else "FALSE",
            "role": self.role if self.role is not None else "",
            "nPoints": self.nPoints,
        }
    
    def save_img(self, img, key):
        space_map.Info("SliceImg Save %s-%s:%s" % (self.index, self.imgKey, key))
        path = "%s/imgs/%s_%s_%s.png" % (self.projectf, self.index, self.imgKey, key)
        if len(img.shape) == 2:
            img = np.stack([img, img, img], axis=-1)
        if len(img.shape) == 3 and img.shape[2] == 4:
            mask = img[:, :, 3]
            img = img[:, :, :3]
            img[mask == 0] = 0
        space_map.imsave(path, img)
        
    def ps(self, dfk):
        return self.get_points(dfk)
    
    def get_points(self, key):
        path1 = "%s/outputs/%s_%s_%s.csv.gz" % (self.projectf, self.index, self.imgKey, key)
        path2 = "%s/outputs/%s_%s_%s.npy" % (self.projectf, self.index, self.imgKey, key)
        if os.path.exists(path1):
            df = pd.read_csv(path1)
            return df[["x", "y"]].values
        elif os.path.exists(path2):
            points = np.load(path2)[:, :2]
            return points
        elif key == Slice.rawKey:
            raise Exception("no Data")
        else:
            space_map.Info("Slice Load %s %s->raw" % (self.index, key))
            return self.get_points(Slice.rawKey)
    
    def get_img(self, key, mchannel=False, scale=True, fixHe=False):
        if self.dfMode:
            points = self.get_points(key)
            img = space_map.show_img(points)
        else:
            path = "%s/imgs/%s_%s_%s.png" % (self.projectf, self.index, self.imgKey, key)
            if not os.path.exists(path):
                if key == Slice.rawKey:
                    raise Exception("no Data")
                space_map.Info("Slice Load %s %s->raw" % (self.index, key))
                return self.get_img(Slice.rawKey, mchannel=mchannel, 
                                    scale=scale, fixHe=fixHe)
            img = cv2.imread(path)
        if len(img.shape) == 3 and not mchannel:
            img = img[:, :, :3]
            img = img.mean(axis=2)
        elif len(img.shape) == 2 and mchannel:
            img = np.stack([img, img, img], axis=2)
        if scale:
            xyd = space_map.XYD
            xyr = space_map.XYRANGE
            shape = (int(xyr/xyd), int(xyr/xyd))
            img = cv2.resize(img, shape)
        if fixHe and self.heMode:
            _, img = space_map.he_img.split_he_background_otsu(img)
        if space_map.IMGCONF.get("raw", 0) == 0:
            img[img > 0] = 1.0
        return img
        
    def save_points(self, points, key):
        space_map.Info("SliceImg Save Points %s-%s:%s" % (self.index, self.imgKey, key))
        # path = "%s/outputs/%s_%s_%s.csv.gz" % (self.projectf, self.index, self.imgKey, key)
        # df = pd.DataFrame(data=points, columns=["x", "y"])
        # df.to_csv(path, index=False)
        path = "%s/outputs/%s_%s_%s.npy" % (self.projectf, self.index, self.imgKey, key)
        np.save(path, points)

    @staticmethod
    def applyH_ps(ps, H):
        return space_map.points.applyH_np(ps, H, fromImgH=True)

    @staticmethod
    def applyH_img(img, H):
        shape = img.shape[0]
        ishape = space_map.XYRANGE / space_map.XYD
        ratio = shape / ishape
        H = H.copy()
        H[0, 2] *= ratio
        H[1, 2] *= ratio
        img = space_map.he_img.rotate_imgH(img, H)
        return img
        
    def applyH(self, fromKey, H, toKey):
        if H is None:
            if self.dfMode:
                points = self.get_points(fromKey)
                self.save_points(points, toKey)
            else:
                img = self.get_img(fromKey, mchannel=True, 
                                   scale=False, fixHe=False)
                self.save_img(img, toKey)
        else:
            if self.dfMode:
                points = self.get_points(fromKey)
                # H_np = spacemap.img.to_npH(H)
                
                points2 = SliceImg.applyH_ps(points, H)
                self.save_points(points2, toKey)
            else:
                img = self.get_img(fromKey, mchannel=True, scale=False, fixHe=False)
                img = SliceImg.applyH_img(img, H)
                self.save_img(img, toKey)
            
    def apply_grid(self, fromKey, toKey, grid, inv_grid=None):
        if grid is None:
            self.applyH(fromKey, None, toKey)
        else:
            if self.dfMode:
                points = self.get_points(fromKey)
                points2, _ = space_map.points.apply_points_by_grid(grid, points, inv_grid)
                self.save_points(points2, toKey)
            else:
                img = self.get_img(fromKey, mchannel=True, scale=False, fixHe=False)
                img1 = space_map.img.apply_img_by_grid(img, grid)
                self.save_img(img1, toKey)
        
    @staticmethod
    def load_config(path, projectf):
        if os.path.exists(path):
            with open(path, "r") as f:
                text = f.read()
                packs = json.loads(text)
            imgs = {}
            for pack in packs.values():
                img = SliceImg(index=pack["index"],
                               imgKey=pack["key"],
                               dfMode=pack["dfMode"] == "TRUE",
                               heMode=pack["heMode"] == "TRUE",
                               projectf=projectf,
                               role=(pack.get("role") or None),
                               nPoints=pack.get("nPoints", 0))
                imgs[img.imgKey] = img
            return imgs
        else:
            return {}

    @staticmethod
    def save_config(imgs, path):
        packs = {}
        for key, img in imgs.items():
            packs[key] = img.to_config()
        with open(path, "w") as f:
            p = json.dumps(packs)
            f.write(p)

class Slice:
    rawKey = "raw"
    align1Key = "align1"
    align2Key = "align2"
    finalKey = "final"
    enhanceKey = "enhance"
    
    def __init__(self, index, projectf=None, first=False):
        self.imgs = {}
        self.index = str(index)
        self.projectf = space_map.BASE if projectf is None else projectf
        self.data = SliceData(index, self.projectf)
        self.first = first
        confPath = "%s/outputs/%s_conf.json" % (self.projectf, self.index)
        self.imgs = SliceImg.load_config(confPath, self.projectf)
        
    def add_img(self, imgKey, heMode):
        img = SliceImg(self.index, imgKey, False, heMode, self.projectf)
        self.imgs[imgKey] = img
        self.save_config()
        
    def _save_points_channel(self, xy, imgKey, role, weight):
        """Register one point-cloud channel from an ``(N, 2)`` xy array.

        Applies the same global APPEND offset as every channel and records the
        channel's weight (sum of the optional count column, else the point
        count) for later affine-score weighting. The stored points are always
        the (offset) x/y; the count only feeds the weight.
        """
        pts = np.asarray(xy, dtype=np.float64).copy()
        pts[:, 0] += space_map.APPEND[0]
        pts[:, 1] += space_map.APPEND[1]
        img = SliceImg(self.index, imgKey, dfMode=True, heMode=False,
                       projectf=self.projectf, role=role, nPoints=int(weight))
        img.save_points(pts, Slice.rawKey)
        self.imgs[imgKey] = img
        return img

    @staticmethod
    def _split_xy_count(arr):
        """Validate a channel array and split it into (xy, weight).

        ``arr`` is ``(N, 2)`` = x/y, or ``(N, 3)`` where the 3rd column is an
        integer count per point. Returns ``(xy, weight)`` where ``weight`` is the
        summed count (``N`` when no count column). Raises on out-of-range xy.
        """
        a = np.asarray(arr, dtype=np.float64)
        if a.ndim != 2 or a.shape[0] == 0:
            raise ValueError("channel array must be a non-empty (N,2) or (N,3) array")
        if a.shape[1] not in (2, 3):
            raise ValueError("channel array must have 2 (x,y) or 3 (x,y,count) columns, got %d" % a.shape[1])
        xy = a[:, :2]
        if not np.isfinite(xy).all():
            raise ValueError("channel coordinates contain NaN/inf")
        if (xy < 0).any():
            raise ValueError("channel coordinates contain negative values")
        xyrange = float(space_map.XYRANGE)
        mx = float(xy.max())
        if mx > xyrange:
            raise ValueError(
                "channel coordinates exceed XYRANGE (%.3g > %d); "
                "rescale inputs or raise space_map.XYRANGE" % (mx, int(xyrange)))
        if a.shape[1] == 3:
            weight = float(np.nansum(a[:, 2]))
        else:
            weight = float(a.shape[0])
        return xy, weight

    @staticmethod
    def _df_to_channels(df):
        """Convert a wide DataFrame to the multi-channel dict.

        Columns ``[x, y, extra1, extra2, ...]``: the first two columns are the
        coordinates; every remaining column becomes its own channel carrying
        ``[x, y, <that column>]``. ``density`` is derived from x/y alone. So
        ``[x, y, celltype, other]`` ->
        ``{"density": [x,y], "celltype": [x,y,celltype], "other": [x,y,other]}``.
        """
        cols = list(df.columns)
        # ``layer``/``index`` identify the slice, not a data channel; drop them.
        reserved = {"layer", "index"}
        if "x" in cols and "y" in cols:
            xcol, ycol = "x", "y"
            extras = [c for c in cols if c not in ("x", "y") and c not in reserved]
        else:
            xcol, ycol = cols[0], cols[1]
            extras = [c for c in cols[2:] if c not in reserved]
        xy = df[[xcol, ycol]].to_numpy(np.float64)
        channels = {"density": xy}
        for c in extras:
            channels[c] = df[[xcol, ycol, c]]
        return channels

    def init_df(self, initdf, celltype_col="celltype", top_n=None):
        """Register the point-cloud input(s) for one slice (single layer).

        ``initdf`` may be:

        * a dict ``{channel_name: array}`` where each array is ``(N,2)`` = x/y or
          ``(N,3)`` = x/y plus an integer count per point (any channel may carry
          it; the count feeds that channel's weight). ``"density"`` is required
          and stored as the primary ``DF`` channel; ``"celltype"`` is expanded to
          one-hot (top-N most abundant); every other key is a gene/expression
          channel. All channels are stored on the slice and transform together.

        * a DataFrame. Columns ``[x, y, extra1, extra2, ...]`` are auto-converted
          to the dict form: x/y become ``density``, and each extra column becomes
          a channel ``[x, y, <col>]`` (``celltype`` expands to one-hot). A plain
          two-column ``x``/``y`` frame is just the density channel (legacy).

        Coordinates are validated: non-finite, negative, or beyond
        ``space_map.XYRANGE`` values raise.
        """
        if not isinstance(initdf, dict):
            if getattr(initdf, "shape", (0, 0))[1] == 0:
                raise Exception("Empty DataFrame")
            channels = Slice._df_to_channels(initdf)
        else:
            channels = dict(initdf)

        if "density" not in channels:
            raise Exception("init_df needs a 'density' channel")
        if top_n is None:
            top_n = space_map.CELLTYPE_TOPN

        # Primary density channel -> DF (keeps every downstream consumer working).
        xy, w = Slice._split_xy_count(np.asarray(channels["density"]))
        self._save_points_channel(xy, SliceImg.DF, role="density", weight=w)

        for name, data in channels.items():
            if name == "density":
                continue
            # celltype expands to one-hot only when it arrives as a labelled
            # DataFrame (the wide-DataFrame path). A bare array under this key has
            # no labels, so it is stored as a single auxiliary channel instead.
            if name == celltype_col and hasattr(data, "columns") \
                    and celltype_col in data.columns:
                self._init_celltype(data, celltype_col, top_n)
            else:
                xy, w = Slice._split_xy_count(Slice._channel_xy(data))
                self._save_points_channel(xy, "gene::%s" % name, role="gene", weight=w)
        self.save_config()

    @staticmethod
    def _channel_xy(data):
        """Coerce a channel value (array or DataFrame) to an xy(+count) array."""
        if isinstance(data, np.ndarray):
            return data
        return data[["x", "y"]].to_numpy(np.float64) if "x" in getattr(data, "columns", []) \
            else np.asarray(data)[:, :2]

    def _init_celltype(self, data, celltype_col, top_n):
        """Expand a cell-type channel to one-hot and keep the top-N types.

        ``data`` is a DataFrame with x/y columns plus ``celltype_col`` (this is
        how the wide-DataFrame path delivers it). Each kept type becomes its own
        auxiliary channel weighted by that type's cell count.
        """
        if not hasattr(data, "columns") or celltype_col not in data.columns:
            raise Exception("celltype channel needs a '%s' column" % celltype_col)
        xcol = "x" if "x" in data.columns else data.columns[0]
        ycol = "y" if "y" in data.columns else data.columns[1]
        counts = data[celltype_col].value_counts()
        for label in counts.index[:top_n]:
            sub = data[data[celltype_col] == label]
            xy, w = Slice._split_xy_count(sub[[xcol, ycol]].to_numpy(np.float64))
            safe = str(label).replace("/", "_").replace(" ", "_")
            self._save_points_channel(xy, "ct::%s" % safe, role="celltype", weight=w)

    def init_img(self, img, he=False, imgKey=None):
        if imgKey is None:
            imgKey = SliceImg.Img
        s = SliceImg(self.index, imgKey,
                       dfMode=False, heMode=he, 
                       projectf=self.projectf)
        s.save_img(img, Slice.rawKey)
        self.imgs[imgKey] = s
        
    def save_config(self):
        confPath = "%s/outputs/%s_conf.json" % (self.projectf, self.index)
        SliceImg.save_config(self.imgs, confPath)
        
    def save_value_img(self, img, imgKey: str, key: str, he=False):
        if imgKey not in self.imgs:
            slice = SliceImg(self.index, imgKey, 
                             dfMode=False, heMode=he, 
                             projectf=self.projectf)
            self.imgs[imgKey] = slice
        slice = self.imgs[imgKey]
        slice.save_img(img, key)
                   
    def save_value_points(self, points, dfKey):
        if SliceImg.DF not in self.imgs:
            slice = SliceImg(self.index, SliceImg.DF,
                                dfMode=True, heMode=False, 
                                projectf=self.projectf)
            self.imgs[SliceImg.DF] = slice
        slice = self.imgs[SliceImg.DF]
        slice.save_points(points, dfKey)
    
    def get_img_raw(self, dfKey):
        return self.get_img(dfKey, mchannel=True, scale=False, fixHe=False)

    def aux_channels(self):
        """Auxiliary point-cloud channels (celltype/gene), i.e. every dfMode
        channel other than the primary density channel (``DF``).

        Returns a list of ``(imgKey, n_points)`` pairs; ``n_points`` is the
        product count used to weight that channel in affine scoring.
        """
        out = []
        for key, img in self.imgs.items():
            if key == SliceImg.DF:
                continue
            if img.dfMode:
                out.append((key, img.nPoints))
        return out

    def density_n_points(self):
        img = self.imgs.get(SliceImg.DF)
        return img.nPoints if img is not None else 0

    def celltype_topk(self):
        """The persisted top-N cell types kept at init, as ``[(label, count)]``.

        Read straight from the stored ``ct::*`` channels (label from the channel
        key, count from its weight) — no re-scan of the raw cell table. Sorted by
        count, most abundant first.
        """
        out = []
        for key, img in self.imgs.items():
            if img.role == "celltype" and key.startswith("ct::"):
                out.append((key[len("ct::"):], int(img.nPoints)))
        out.sort(key=lambda kv: kv[1], reverse=True)
        return out

    def all_ps(self, dfKey):
        """Every point-cloud channel's points at ``dfKey``, as ``{imgKey: (N,2)}``.

        Includes density (``DF``) and all auxiliary channels. Useful for
        exporting or inspecting all channels of a slice at once.
        """
        out = {}
        for key, img in self.imgs.items():
            if img.dfMode:
                out[key] = img.get_points(dfKey)
        return out

    def get_multi_img(self, dfKey, scale=True, fixHe=False,
                      include_density=True):
        """Render every point-cloud channel of this slice as a separate image.

        Returns ``(keys, imgs, weights)`` where each ``imgs[i]`` is the 2D image
        of channel ``keys[i]`` and ``weights[i]`` is that channel's weight
        (``SliceImg.nPoints`` — summed count / point count). The density channel
        (``DF``) comes first when ``include_density`` is set.

        This is the multi-channel view consumed by affine scoring: channels are
        kept separate (each compared on its own), and the weights say how much
        each channel counts toward the combined alignment score.
        """
        keys, imgs, weights = [], [], []
        if include_density and SliceImg.DF in self.imgs:
            keys.append(SliceImg.DF)
        for key, img in self.imgs.items():
            if img.dfMode and key != SliceImg.DF:
                keys.append(key)
        for key in keys:
            imgs.append(self.imgs[key].get_img(dfKey, mchannel=False,
                                               scale=scale, fixHe=fixHe))
            weights.append(float(self.imgs[key].nPoints))
        return keys, imgs, weights

    def get_img(self, imgKey, dfKey, mchannel=False, scale=True, fixHe=False):
        if imgKey not in self.imgs:
            raise Exception("No Image")
        return self.imgs[imgKey].get_img(dfKey, mchannel=mchannel, 
                                         scale=scale, fixHe=fixHe)
        
    def create_img(self, imgKey, dfKey, 
                   mchannel=False, scale=True, fixHe=False):
        return self.get_img(imgKey, dfKey, 
                            mchannel=mchannel, scale=scale, fixHe=fixHe)
        
    def applyH(self, fromDF, H, toDF):
        for img in self.imgs.values():
            img.applyH(fromDF, H, toDF)
            
    def ps(self, key):
        return self.imgs["DF"].ps(key)
            
    def apply_grid(self, fromDF, toDF, grid, inv_grid=None):
        if grid is None and inv_grid is not None:
            if SliceImg.DF in self.imgs.keys() and len(self.imgs.keys()) > 1:
                grid = space_map.points.inverse_grid_train(inv_grid)
        for img in self.imgs.values():
            img.apply_grid(fromDF, toDF, grid, inv_grid)
    
    @staticmethod
    def show_align(sI, sJ, keyI=None, keyJ=None, imgKey=SliceImg.Img):
        keyI = Slice.finalKey if keyI is None else keyI
        keyJ = Slice.rawKey if keyJ is None else keyJ
        if imgKey not in sI.imgs or imgKey not in sJ.imgs:
            raise Exception("No Image %s" % imgKey)
        space_map.Info("Slice Align: %s-%s %s-%s" % (sI.index, keyI, sJ.index, keyJ))
        if imgKey != SliceImg.DF:
            imgI = sI.get_img(imgKey, keyI, mchannel=False, scale=True, fixHe=True)
            imgJ = sJ.get_img(imgKey, keyJ, mchannel=False, scale=True, fixHe=True)
            space_map.show_compare_channel(imgI, imgJ, titleI=sI.index, titleJ=sJ.index)
        else:
            psI = sI.imgs[imgKey].get_points(keyI)
            psJ = sJ.imgs[imgKey].get_points(keyJ)
            dfI = pd.DataFrame(data=psI, columns=["x", "y"])
            dfJ = pd.DataFrame(data=psJ, columns=["x", "y"])
            space_map.show_xy([dfI, dfJ], 
                            ["Target_" + str(sI.index), "New_" + str(sJ.index)], 
                            keyx="x", 
                            keyy="y", s=0.1, alpha=0.2)
        