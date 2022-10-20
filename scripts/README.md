# Golden ratio sampling scripts

These are scripts to support learning about spatial sampling with the golden ratio, particularly sampling along paths. As the main README explains, the intent is to provide useful snippets, not a standalone library. The rest of this README walks through one (rather idiosyncratic) way of generating viewsheds of the Wonderland Trail.

## A viewshed demo

Here’s how to make a demo of lighting up a composite viewshed with golden ratio sampling, as Eric showed in his NACIS talk. (Probably. I’m writing this just before he’s giving his talk, and he has like 40 minutes of material to do in 20 minutes, so we’ll see.)

This walkthrough assumes an intermediate amount of geospatial data processing experience. You should be familiar with terms like CRS and warping. It is _what I did_, not necessarily _the best way to do this_.

### Requirements

To follow the exact steps listed here, you will need a Unix-like system (Linux, macOS, etc.) with:

- Enough command-line experience to follow the rough spots where I accidentally forget to mention you need to `cd` somewhere (or something) and you’ll have to get it from context
- A good amount of processing power to work with large files reasonably quickly
- The [GDAL](https://gdal.org/) command-line tools, for various geospatial operations
- [GNU parallel](https://www.gnu.org/software/parallel/), for templating complex iteration in the shell (basically letting you construct loops that you would otherwise want to drive with python-or-whatever)
- A modern python installation with libraries including `gpxpy`, `pyproj`, and `click`

### Getting the data

We’ll use the Wonderland Trail, a loop around Mt Rainier. So to start with, head to the [Washington lidar portal](https://lidarportal.dnr.wa.gov/#46.84176:-121.78448:12) and get the DTM for Rainier 2007. We’ll break this into building a VRT:

```sh
gdalbuildvrt all.vrt datasetsA/rainier_2007/dtm/rainier_2007_dtm_*
```

And then warping that to a giant TIFF (you could probably add a `-co compress=deflate` here and not regret it):

```sh
gdalwarp -t_srs EPSG:32610 -tr 10 10 -multi -r bilinear all.vrt all.tif
```

[EPSG:32610](https://epsg.io/32610) is Mt Rainier’s UTM zone. Naturally you can use whatever makes sense.

Now let’s convert from “feet” to meters, set a nodata value, and put it in integers:

```sh
gdal_translate -scale 0 1 0 0.3048 -a_nodata 0 -ot uint16 all.tif all_m.tif
```

You can do all this in fewer commands, but this way leaves nicer breadcrumbs for debugging.

Now we want the Wonderland Trail. Pull up [Overpass Turbo](https://overpass-turbo.eu/) and run this query:

```
[out:json][timeout:25];
(
  relation(4111743);
);
out body;
>;
out skel qt;
```

You should see the Wonderland Trail lit up if you look for it. Go to `Export` → `Data` → `GPX` → `download`. Save this as `wonderland.gpx`.

“Say, don’t you prefer geoJSON to GPX when you have the choice?” I sure do, but I was asking friends for GPX traces from hikes they’d taken, so that’s how I wrote this. The scripting should be _very_ easy to convert.


## Generating points

Now let’s query out some points. You can actually skip this step; I just want you to see what the output looks like.

```
python gpx_sampler.py -c -s "," wonderland.gpx phi ..249 32610
```

That is, sample:

- `-c` with a counter number in the output (so we can number our viewshed frames)
- `-s ","` with the separator `,`
- `wonderland.gpx` reading out of that file
- `phi` in steps of the golden ratio
- `..249` sample points 0 through 249
- `32610` in EPSG:32610, which also means the output units are meters

The output should end:

```
240,+584363.758498,+5195124.165887
241,+604181.635577,+5191468.320404
242,+587908.757987,+5183630.152816
243,+591770.818035,+5200207.385320
244,+605064.506393,+5180809.102239
245,+584082.394638,+5190067.584945
246,+602163.954399,+5196111.680332
247,+591316.982484,+5179048.269133
248,+586327.079590,+5198617.028123
249,+602338.758883,+5188284.031964
```

So we have a CSV of sample number, x coordinate, y coordinate. We could save this and read it back in, but let’s do it live for `parallel`.


## Generating images

First let’s make somewhere for our individual viewshed images to go:

```
mkdir wonderland-phi-points
```

Now we’re going to run the `gpx_sampler.py` query again, but this time using it as input for a `parallel` template for `gdal_viewshed`. This is going to look scary at first but notice, for a start, that everything after `:::` is what we already saw, and could be replaced by reading points saved to a file. You can run all this with the `--dry-run` flag to `parallel` to see it templated out without running it. So here’s the core of this whole process:

```sh
parallel -j3 --colsep "," gdal_viewshed -co compress=lzw -cc 0.85714 -oz 2 -ox {2} -oy {3} all_m.tif /{1}.tif ::: $(python gpx_sampler.py -c -s "," wonderland.gpx phi ..249 32610)
```

Okay, first the `parallel` flags:

- `-j3` use 3 workers – adjust this heuristically
- `--colsep ","` parse input as CSV
- `:::` everything after this is the template input
- `{2}` everything in curly braces is template variables, named for their 1-based column in the CSV

And `gdal_viewshed`’s:

- `-co compress=lzw` throw some quick compression on here, because these images add up quickly
- `-cc 0.85714` set a curvature coefficient manually – I don’t think you should need this but I think I was getting iffy results from the default when I was working on other data; consider this a FIXME
- `-oz 2` calculate viewshed for a viewer 2 m above the nominal surface (this is pretty conservative; standing on a rock in the tallest part of a pixel would probably get you to 4 m)
- `-ox {2} -oy {3}` take x and y coordinates from the CSV

After you run this, you should have 250 viewshed images, each sampled another φth of the way around the loop of the Wonderland Trail, in `wonderland-phi-points`.

## Ways forward

Since phi sampling is deterministic, you can regenerate those points to, for example, draw a marker on each frame. You can collect the images into a cumulative average. You can just average them together and get a kind of multi-angle hillshade, amounting to a visibility index w/r/t the Wonderland Trail. You can re-run `gpx_sampler.py` with a non-phi fractional step (say, 1/250 if you’re sampling 250 points) and compare. Et cetera. Have fun!

