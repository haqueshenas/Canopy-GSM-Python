<div align="center">

<img src="CanopyGSM.png" alt="Canopy GSM logo" width="220">

<h1>Canopy GSM for Python</h1>

<strong>Green-gradient based Canopy Segmentation Model for quantitative RGB crop-canopy analysis</strong>

<br>

Version 1.0.0 · Free and open-source crop-phenotyping software

<a href="https://doi.org/10.5281/zenodo.23134465">
<img src="https://zenodo.org/badge/DOI/10.5281/zenodo.23134465.svg" alt="DOI">
</a>

<br><br>

<a href="https://github.com/haqueshenas/Canopy-GSM-Python/releases/latest">
Download Windows application
</a>

&nbsp; · &nbsp;

<a href="https://doi.org/10.1016/j.compag.2020.105740">
Scientific paper
</a>

&nbsp; · &nbsp;

<a href="https://haqueshenas.github.io/EPL/">
Easy-Phenotyping Lab (EPL)
</a>

<br><br>

<em>
Explore 2D crop-canopy images with GSM, quantify shading patterns from RGB triplets,
generate a versatile GSM graph, and obtain quantitative image-derived outputs for
canopy studies, crop phenotyping, and data mining.
</em>

</div>

---

## Contents

- [1. What is Canopy GSM?](#1-what-is-canopy-gsm)
- [2. Quick start](#2-quick-start)
- [3. Scientific basis](#3-scientific-basis)
- [4. From MATLAB to Python](#4-from-matlab-to-python)
- [5. What the GSM graph represents](#5-what-the-gsm-graph-represents)
- [6. ST1, ST2, and ST3](#6-st1-st2-and-st3)
- [7. Scientific workflow](#7-scientific-workflow)
- [8. Installation and distribution](#8-installation-and-distribution)
- [9. Input image requirements](#9-input-image-requirements)
- [10. Launching the application](#10-launching-the-application)
- [11. Choosing a workflow](#11-choosing-a-workflow)
- [12. Batch Processing](#12-batch-processing)
- [13. Batch Processing settings](#13-batch-processing-settings)
- [14. Batch Processing step-by-step procedure](#14-batch-processing-step-by-step-procedure)
- [15. Batch Processing outputs](#15-batch-processing-outputs)
- [16. Understanding the 22-column GSM result table](#16-understanding-the-22-column-gsm-result-table)
- [17. Aggregate Batch tables](#17-aggregate-batch-tables)
- [18. Batch logging](#18-batch-logging)
- [19. Canopy GSM Explorer](#19-canopy-gsm-explorer)
- [20. Explorer toolbar](#20-explorer-toolbar)
- [21. Explorer settings](#21-explorer-settings)
- [22. Applying ST1 in Explorer](#22-applying-st1-in-explorer)
- [23. Building the GSM graph](#23-building-the-gsm-graph)
- [24. Interactive Green-range selection](#24-interactive-green-range-selection)
- [25. Reverse selection](#25-reverse-selection)
- [26. GSM graph controls and interpretation](#26-gsm-graph-controls-and-interpretation)
- [27. ST3 markers and labels](#27-st3-markers-and-labels)
- [28. Optional curve fitting](#28-optional-curve-fitting)
- [29. Zoom, pan, and cursor inspection](#29-zoom-pan-and-cursor-inspection)
- [30. Explorer export](#30-explorer-export)
- [31. Explorer output files](#31-explorer-output-files)
- [32. Background color](#32-background-color)
- [33. Custom ST1 segmentation](#33-custom-st1-segmentation)
- [34. Reproducibility](#34-reproducibility)
- [35. Scientific considerations](#35-scientific-considerations)
- [36. Troubleshooting](#36-troubleshooting)
- [37. Project structure](#37-project-structure)
- [38. Historical MATLAB implementation](#38-historical-matlab-implementation)
- [39. Citation](#39-citation)
- [40. Authors, development, and license](#40-authors-development-and-license)
- [41. Frequently asked questions](#41-frequently-asked-questions)

---

# 1. What is Canopy GSM?

**Canopy GSM for Python** is an open-source scientific image-analysis application
built around the **Green-gradient based Canopy Segmentation Model (GSM)**.

GSM provides a quantitative, image-based representation of crop canopies from
two-dimensional RGB images. Rather than treating a canopy photograph only as a
visual image, GSM treats vegetation pixels as a structured RGB population and
examines the relative behavior of the Red and Blue channels along a Green
gradient.

This provides a quantitative way to characterize canopy structure and,
particularly, to investigate patterns associated with illumination and shading.

The central GSM process is:

1. identify vegetation pixels;
2. organize the vegetation pixels according to their Green level;
3. calculate the mean Red and mean Blue values associated with each Green level;
4. represent those values as the principal GSM curves;
5. derive additional numerical variables from the resulting GSM data.

The Green levels span:

```text
1, 2, 3, ... , 255
```

for the image-based GSM representation.

The principal GSM graph therefore contains two image-derived response patterns:

```text
Mean Red  versus Green level
Mean Blue versus Green level
```

The relative behavior of these Red and Blue patterns across the Green gradient
provides a quantitative representation of canopy variation that can be used to
study shading patterns in two-dimensional crop-canopy imagery.

The original scientific study introduced GSM specifically as a simple image
mining technique for the quantitative characterization of shading patterns in
crop canopies. The method is based on relative variations in RGB triplets under
different illumination conditions. Vegetation pixels are categorized into up to
255 Green-level groups, and the mean Red and Blue values of those groups are
plotted against Green level.

The resulting GSM graph can be used for:

- identifying and characterizing crop canopies;
- classifying canopy pixels according to their degree of exposure to sunlight;
- generating quantitative image-derived variables;
- supporting data-mining and high-throughput phenotyping approaches;
- investigating canopy shading patterns and canopy-related variation.

GSM should therefore be understood as a **quantitative image-derived
characterization and representation of crop-canopy structure and shading-related
variation**, rather than as a replacement for botanical or ecological
definitions of a canopy.

Canopy GSM can be useful in:

- crop science;
- agronomy;
- crop production;
- plant physiology;
- plant breeding;
- crop phenotyping;
- canopy studies;
- image-based phenotyping;
- image mining;
- investigation of environmental and management effects on crop canopies.

The software provides practical image processing together with transparent
numerical and graphical outputs for scientific analysis.

---

# 2. Quick start

## Windows application

The simplest way to use Canopy GSM is the standalone Windows application.

### Step 1 — Download

Download the Windows application from the latest release:

[Download Canopy GSM for Windows](https://github.com/haqueshenas/Canopy-GSM-Python/releases/latest)

The v1.0.0 package is distributed as:

```text
CanopyGSM-v1.0.0-Windows-x64.zip
```

### Step 2 — Extract the complete application directory

Extract the ZIP as a complete application directory.

The packaged application is not intended to be separated into individual
files.

The extracted structure contains:

```text
CanopyGSM\
    CanopyGSM.exe
    _internal\
    ...
```

### Step 3 — Launch

Run:

```text
CanopyGSM.exe
```

No separate Python installation is required for the packaged Windows
application.

### Step 4 — Choose a workflow

The Launcher provides:

```text
Batch Processing
Canopy GSM Explorer
About
```

Choose **Batch Processing** to process an image collection.

Choose **Canopy GSM Explorer** to investigate one image interactively.

### Step 5 — Try the sample data

The repository includes demonstration images in:

```text
Data/Sample_Data/
```

The sample images are provided so that the software can be tried without first
preparing a personal image collection.

---

# 3. Scientific basis

The underlying GSM methodology is described in:

> Haghshenas, A., & Emam, Y. (2020).
> *Green-gradient based canopy segmentation: A multipurpose image mining model
> with potential use in crop phenotyping and canopy studies.*
> Computers and Electronics in Agriculture, 178, 105740.

**DOI:**

https://doi.org/10.1016/j.compag.2020.105740

The published study introduced GSM as a simple image-mining technique designed
to evaluate the option of quantitatively characterizing shading patterns inside
crop canopies from two-dimensional ground-based nadir RGB images.

The method is based on the relative variation of RGB triplets under different
illumination conditions.

Vegetation pixels are categorized according to their Green levels, with up to
255 possible Green-level groups. The mean Red and mean Blue values of the
pixels belonging to each Green level are then calculated and plotted against
the ascending Green-level sequence.

The resulting graph provides a quantitative representation of the Red and Blue
responses along the Green gradient.

The published study reports several uses of the GSM graph, including:

- identifying and characterizing crop canopies using one or two equations;
- classifying canopy pixels according to their degree of exposure to sunlight;
- generating quantitative variables for image mining and phenotyping;
- predicting or relating image-derived canopy characteristics to experimental
  variables such as canopy coverage and canopy temperature;
- classifying experimental conditions represented in the image data.

The study therefore presents GSM as a multipurpose image-mining framework for
crop-canopy studies and high-throughput phenotyping.

The software does not directly measure every biological, physiological, or
environmental variable that may be investigated in a research study. GSM
extracts structured quantitative information from RGB imagery that can be
combined with experimental and phenotypic measurements.

For scientific interpretation, the original experimental design, image
acquisition conditions, and biological context remain essential.

---

# 4. From MATLAB to Python

The historical Canopy GSM software was distributed as a MATLAB implementation
and is identified in the historical repository as **Version 2.1**.

Historical resources include:

- Historical GitHub repository:
  https://github.com/haqueshenas/Canopy-GSM
- Code Ocean:
  https://codeocean.com/capsule/1652693/tree/v2

The historical MATLAB software contains the original GSM workflow, including
ST1, GSM graph generation, ST3, exponential fitting, individual result tables,
and aggregate GSM tables.

The present software is deliberately called:

**Canopy GSM for Python — Version 1.0.0**

It is a **new Python software line**, not "MATLAB Version 3".

The relationship is:

```text
Historical Canopy GSM
MATLAB Version 2.1
        │
        │ historical scientific and software reference
        ▼
Canopy GSM for Python
Version 1.0.0
```

The Python implementation retains the established GSM scientific calculation
concept while providing a modern Python implementation and a Windows-oriented
graphical application.

The Python application also provides application- and interaction-level
functionality such as:

- a unified Launcher;
- Batch Processing;
- Canopy GSM Explorer;
- live processed-image visualization;
- interactive Green-range selection;
- Reverse selection;
- dynamic graph highlighting;
- optional interactive curve fitting;
- ST3 markers and labels;
- graph cursor inspection;
- image and graph zoom;
- mouse and keyboard panning;
- vector PDF graph export;
- full-resolution PNG export;
- human-readable analysis records.

These application-level capabilities should be distinguished from the
scientific definition of GSM itself.

---

# 5. What the GSM graph represents

The GSM graph uses Green level as its horizontal coordinate.

The Green levels are:

```text
G = 1, 2, 3, ... , 255
```

For each Green level, the vegetation pixels belonging to that level are
examined.

The two principal GSM curves are:

```text
Mean Red  versus Green level
Mean Blue versus Green level
```

The scientific result also contains, among other variables:

- mean Red value;
- Green level;
- mean Blue value;
- Red variance;
- Blue variance;
- number of contributing pixels;
- Red cumulative area information;
- Blue cumulative area information;
- Red/Blue area-related difference;
- Red local slope;
- Blue local slope;
- Red ST3 classification;
- Blue ST3 classification;
- Red exponential-fit statistics;
- Blue exponential-fit statistics.

The Green sequence provides the reference coordinate, while the Red and Blue
means provide the image-derived responses associated with each Green level.

The published GSM work describes the resulting Red and Blue patterns as
upward, exponential-shaped curves and uses their relative behavior to
characterize the canopy and its shading-related distribution.

The GSM graph is therefore more than a simple color histogram. It provides a
structured image-derived representation of vegetation behavior along a
Green-gradient coordinate.

---

# 6. ST1, ST2, and ST3

The GSM workflow contains three conceptually different processing layers.

## ST1 — vegetation segmentation

**Segmentation Type 1 (ST1)** is the first segmentation step. It separates
vegetation pixels from background or other non-vegetation pixels.

The default ST1 method is:

```text
G > R
```

A pixel is classified as vegetation when its Green component is greater than
its Red component.

Available ST1 methods are:

```text
G>R
G>R&G>B
2G-R-B>0
HSV
CUSTOM
```

### `G>R`

```text
G > R
```

This is the default GSM-compatible RGB rule.

### `G>R&G>B`

```text
G > R
and
G > B
```

This is more restrictive than `G>R`.

### `2G-R-B>0`

```text
2G - R - B > 0
```

This provides another RGB green-contrast rule.

### HSV

HSV is an additional Python segmentation method.

The default HSV bounds are:

```text
H: 25 – 95
S: 40 – 255
V: 30 – 255
```

These are **ranges**, not individual fixed values.

A pixel is selected only when its Hue, Saturation, and Value are all within
their respective specified minimum and maximum bounds.

OpenCV represents:

```text
Hue        0 – 179
Saturation 0 – 255
Value      0 – 255
```

Changing the ST1 method or its parameters changes the vegetation mask and can
therefore change all downstream GSM numerical results.

### CUSTOM

The Python application also supports a custom ST1 method supplied as an
external Python file.

The file defines:

```python
create_mask(image)
```

and returns a Boolean or binary mask having the same height and width as the
input image.

---

## ST2 — the core GSM green-gradient analysis

**Segmentation Type 2 (ST2)** is the main quantitative GSM analysis.

The vegetation pixels selected by ST1 are organized into Green levels from
1 through 255.

For each Green level, the corresponding Red and Blue information is calculated.
The resulting values form the principal GSM curves and the associated
scientific GSM variables.

ST2 is therefore the central quantitative GSM layer.

---

## ST3 — curve-derived segmentation and classification

**Segmentation Type 3 (ST3)** is a downstream curve-segmentation and
classification layer based on the behavior of the Red and Blue GSM curves.

ST3 examines the sequences of local Red and Blue slopes along the Green
gradient and identifies regions where curve behavior changes.

The current default values are:

```text
P = 50
m = 12
```

These parameters belong to the ST3 procedure.

The procedure scans the Red or Blue slope sequence along the Green-level axis
and uses the configured ST3 parameters to identify curve segments and their
boundaries. The Green 1:1 line provides the underlying Green-gradient
reference used in interpreting slope behavior.

The purpose of ST3 is to help identify different curve-derived regions that can
be associated with different degrees of canopy light exposure, ranging from
more directly exposed vegetation through intermediate conditions to deeper
shading.

ST3 is not a universal biological classifier. Its classes can depend strongly
on:

- canopy condition;
- illumination;
- phenological stage;
- environmental stress;
- image characteristics;
- experimental conditions.

The current release provides one ST3 algorithm.

Users may investigate or develop alternative ST3 methods at source-code level
for specific research applications; see the FAQ and the `st3.py` description
in the Project structure section.

Changing ST3 parameters changes ST3 classifications and boundaries. It does
not redefine the upstream ST2 Red and Blue GSM curve values.

---

# 7. Scientific workflow

Canopy GSM provides two complementary workflows.

## Batch Processing

```text
Folder of images
       │
       ▼
      ST1
       │
       ▼
      ST2
       │
       ├── 255 Green levels
       ├── Red/Blue GSM curves
       ├── numerical GSM variables
       ├── ST3 classifications
       └── exponential fitting
       │
       ▼
CSV tables + processed images + GSM graphs + log
```

## Canopy GSM Explorer

```text
One image
    │
    ▼
Open Image
    │
    ▼
Apply ST1
    │
    ▼
Build GSM Graph
    │
    ▼
Interactive Green-range selection
    │
    ├── image filtering
    ├── graph highlighting
    ├── Reverse selection
    ├── ST3 inspection
    ├── optional fitting
    └── cursor inspection
    │
    ▼
Export
```

A central design principle is that the scientific GSM calculation follows one
authoritative processing path.

The GUI is a presentation and interaction layer around the scientific engine.

Explorer does not silently create a second independent GSM calculation for an
interactive range selection.

After a GSM result has been built, changing the Green range filters the
existing result for interactive analysis rather than rebuilding the complete
scientific result from the original image.

The distinction is:

```text
Underlying GSM scientific result
                ≠
Interactive Explorer selection
```

---

# 8. Installation and distribution

Canopy GSM for Python is free and open-source software released under the
MIT License.

The primary packaged distribution is a standalone Windows x64 application.

## Windows application package

The packaged Windows application is distributed through the GitHub Releases
section.

The v1.0.0 package is:

```text
CanopyGSM-v1.0.0-Windows-x64.zip
```

The ZIP contains the complete packaged application directory.

Extract the complete directory before running the application.

The executable should be run from that directory:

```text
CanopyGSM\
    CanopyGSM.exe
    _internal\
    ...
```

Do not move `CanopyGSM.exe` outside its accompanying application directory.

No separate Python installation is required for the packaged Windows
application.

## Running from source

Developers and researchers may run the Python source directly.

The project uses:

```text
Python
NumPy
SciPy
OpenCV
Matplotlib
PySide6
```

The current project has been developed with Python 3.13.

A source installation requires Python and the project dependencies.

The application entry point is:

```text
canopy_gsm.py
```

A typical source execution is:

```text
python canopy_gsm.py
```

The repository also includes:

```text
CanopyGSM.spec
```

for building the Windows application package with PyInstaller.

---

# 9. Input image requirements

Canopy GSM for Python has a deliberately strict image-input contract.

Supported image extensions are:

```text
.jpg
.jpeg
.png
.tif
.tiff
.bmp
.webp
```

The input image must be a:

```text
8-bit
3-channel
RGB
```

image.

This requirement is intentional.

The software does not silently make an unsuitable image acceptable by changing
its pixel representation.

The following are rejected:

- grayscale images;
- RGBA or four-channel images;
- images with other channel counts;
- non-8-bit images;
- uint16 or other unsupported image depths;
- Bayer or RAW data requiring demosaicing;
- HEIC or HEIF images.

In particular:

```text
Grayscale → not silently converted to RGB

RGBA → not silently stripped to RGB

uint16 → not silently rescaled to uint8

RAW/Bayer → not automatically demosaiced
```

Strict input handling protects reproducibility because hidden conversions can
change the pixel values supplied to the scientific calculation.

The application may use OpenCV internally for image decoding, but the
scientific engine operates under the RGB uint8 input contract.

---

# 10. Launching the application

The normal user experience starts with the **Canopy GSM Launcher**.

Launch:

```text
CanopyGSM.exe
```

The Launcher provides:

```text
Batch Processing
Canopy GSM Explorer
About
```

The About dialog provides software identity and project information.

---

# 11. Choosing a workflow

## Batch Processing

Choose **Batch Processing** when you need to process a collection of images
using one consistent analysis configuration.

Typical use:

```text
Image collection
       ↓
One ST1 configuration
       ↓
One batch run
       ↓
Structured numerical and graphical outputs
```

## Canopy GSM Explorer

Choose **Canopy GSM Explorer** when you want to investigate one image
interactively.

Typical use:

```text
One image
   ↓
ST1
   ↓
GSM graph
   ↓
Green-range selection
   ↓
Image and graph inspection
   ↓
ST3 inspection
   ↓
Optional fitting
   ↓
Export
```

Explorer is an analytical workspace rather than merely an image preview.

---

# 12. Batch Processing

Batch Processing is designed for repeated analysis of an image collection.

The interface provides:

- input folder selection;
- output folder selection;
- scientific settings;
- Live Processed Image;
- Live GSM Graph;
- processing controls;
- status and logging.

The two principal visual panels are:

```text
Live Processed Image
Live GSM Graph
```

The visualizations help users inspect the processing state while the numerical
CSV files remain the principal machine-readable outputs.

The Batch GSM graph displays data points rather than decorative connecting
vectors.

---

# 13. Batch Processing settings

## ST1 segmentation method

The default ST1 method is:

```text
G>R
```

The default is **not HSV**.

Available methods are:

| Method | Rule | Description |
|---|---|---|
| `G>R` | `G > R` | Default GSM-compatible RGB rule |
| `G>R&G>B` | `G > R` and `G > B` | More restrictive RGB vegetation rule |
| `2G-R-B>0` | `2G - R - B > 0` | RGB green-contrast rule |
| `HSV` | H/S/V ranges | HSV-based segmentation extension |
| `CUSTOM` | Python mask function | User-supplied ST1 segmentation |

### HSV thresholds

HSV settings are expressed as ranges:

```text
H min ≤ H ≤ H max
S min ≤ S ≤ S max
V min ≤ V ≤ V max
```

The default values are:

```text
H: 25 – 95
S: 40 – 255
V: 30 – 255
```

A pixel is selected only when all three HSV channels satisfy their respective
ranges.

### Custom ST1

The Custom ST1 option accepts an external Python file defining:

```python
create_mask(image)
```

The function should return a Boolean or binary mask having the same height and
width as the input image.

---

## ST3 parameters

The default ST3 parameters are:

```text
P = 50
m = 12
```

They control the downstream ST3 curve-segmentation/classification procedure.

Changing ST3 parameters changes ST3 classifications but does not change the
upstream ST2 Red and Blue GSM curve values.

---

## Processed-image background

The default processed-image background is:

```text
Purple (150, 0, 150)
```

The background controls the appearance of processed/exported segmentation
images.

It does not change:

- ST1 classification;
- ST2 numerical GSM values;
- ST3 classifications;
- exponential fitting.

A custom RGB background can also be selected.

---

# 14. Batch Processing step-by-step procedure

## Step 1 — Launch the application

Launch Canopy GSM for Python.

## Step 2 — Open Batch Processing

Select:

```text
Batch Processing
```

## Step 3 — Select the input folder

Choose the folder containing supported RGB images.

For comparative scientific work, images should be acquired under comparable
imaging conditions.

## Step 4 — Select the output folder

Choose where Canopy GSM should save the generated outputs.

## Step 5 — Choose ST1

Select the required segmentation method.

The default is:

```text
G>R
```

When HSV is selected, specify the desired H, S, and V ranges.

When Custom is selected, provide the Python segmentation file.

## Step 6 — Review ST3

The defaults are:

```text
P = 50
m = 12
```

Specify alternative values when required by the study.

## Step 7 — Review the processed-image background

The default is:

```text
Purple (150, 0, 150)
```

## Step 8 — Inspect the live visualization

The Live Processed Image and Live GSM Graph provide visual information about
the current processing state.

The scientific calculation operates on the original image data rather than a
resized screen preview.

## Step 9 — Start processing

Press:

```text
START PROCESSING
```

The application processes the image collection through the GSM scientific
engine.

## Step 10 — Review the outputs

After processing, inspect:

- individual result CSV files;
- aggregate GSM CSV files;
- processed PNG images;
- GSM PDF graphs;
- batch log.

---

# 15. Batch Processing outputs

For each processed image, the principal outputs are:

```text
Results of image <filename>.csv
Processed_<image-stem>.png
Graphs of image <filename>.pdf
```

The processed image is a PNG representation of the ST1 segmentation.

The GSM graph is exported as a PDF.

The Batch workflow also produces:

```text
Total GSM ST2.csv
Total GSM Num.csv
Total GSM Exp.csv
```

These aggregate tables are designed for downstream analysis, statistics,
data mining, and phenotyping workflows.

---

# 16. Understanding the 22-column GSM result table

Each individual GSM scientific result contains 22 columns.

| # | Column | Meaning |
|---:|---|---|
| 1 | `Green_level` | Green level from 1 to 255 |
| 2 | `Mean_Red` | Mean Red value at the Green level |
| 3 | `Green` | Green-level coordinate |
| 4 | `Mean_Blue` | Mean Blue value at the Green level |
| 5 | `Var_Red` | Red variance |
| 6 | `Var_Blue` | Blue variance |
| 7 | `Number_of_pixels` | Number of contributing vegetation pixels |
| 8 | `Red_AUC` | Cumulative Red-curve area value |
| 9 | `Blue_AUC` | Cumulative Blue-curve area value |
| 10 | `RB_ABC` | Difference between Red and Blue cumulative areas |
| 11 | `Red_Slope` | Local Red-curve slope |
| 12 | `Blue_slope` | Local Blue-curve slope |
| 13 | `Red_ST3_class` | ST3 class of the Red curve |
| 14 | `Blue_ST3_class` | ST3 class of the Blue curve |
| 15 | `R2_exp_Red` | R² of the Red exponential fit |
| 16 | `RMSE_exp_Red` | RMSE of the Red exponential fit |
| 17 | `exp_a_Red` | Red exponential coefficient `a` |
| 18 | `exp_b_Red` | Red exponential coefficient `b` |
| 19 | `R2_exp_Blue` | R² of the Blue exponential fit |
| 20 | `RMSE_exp_Blue` | RMSE of the Blue exponential fit |
| 21 | `exp_a_Blue` | Blue exponential coefficient `a` |
| 22 | `exp_b_Blue` | Blue exponential coefficient `b` |

The scientific result contains 255 Green-level rows.

---

# 17. Aggregate Batch tables

## `Total GSM ST2.csv`

This table collects the Red and Blue GSM curves for all processed images.

Its structure is:

```text
Image
R_G1 ... R_G255
B_G1 ... B_G255
```

There are:

```text
1 + 255 + 255 = 511 columns
```

The first 255 curve values represent the Red GSM data.

The second 255 values represent the Blue GSM data.

---

## `Total GSM Num.csv`

This table collects the number of contributing pixels at each Green level.

Its structure is:

```text
Image
G1 ... G255
```

There are:

```text
1 + 255 = 256 columns
```

---

## `Total GSM Exp.csv`

This table collects the exponential-fitting statistics for all processed
images.

Its structure is:

```text
Image
R2_exp_Red
RMSE_exp_Red
Exp_a_Red
Exp_b_Red
R2_exp_Blue
RMSE_exp_Blue
Exp_a_Blue
Exp_b_Blue
```

There are:

```text
9 columns
```

This table is useful when comparing fitted GSM characteristics among images.

---

# 18. Batch logging

Each Batch run produces a processing log in the selected output area.

The log records useful information such as:

- software version;
- input folder;
- output folder;
- date and time;
- scientific settings;
- ST1 method;
- ST3 parameters;
- background setting;
- number of images;
- successfully processed images;
- failed images;
- processing duration;
- error information when applicable.

The log is intended as a human-readable record of the processing event.

---

# 19. Canopy GSM Explorer

**Canopy GSM Explorer** is a one-image interactive analytical workspace.

It is designed for detailed investigation of:

- ST1 segmentation;
- GSM graph behavior;
- Green-level ranges;
- image filtering;
- graph highlighting;
- Reverse selection;
- ST3 boundaries;
- curve fitting;
- cursor inspection;
- zoom and pan;
- export.

Explorer uses one image at a time.

Its intended workflow is:

```text
Open Image
    ↓
Apply ST1
    ↓
Build GSM Graph
    ↓
Inspect and select
    ↓
Optional fitting
    ↓
Export
```

Explorer does not rerun the complete Batch workflow every time the user
changes an interactive selection.

---

# 20. Explorer toolbar

The main Explorer controls include:

```text
Open Image
Apply ST1
Build GSM Graph
Reset
Image path
Settings
Export
```

## Open Image

Opens one supported RGB uint8 image.

Opening a new image starts a new Explorer analysis state.

## Apply ST1

Applies the selected ST1 segmentation to the original full-resolution image.

The result is shown as vegetation against the selected background.

Applying a new ST1 segmentation invalidates the previously built GSM graph
because the underlying vegetation mask has changed.

## Build GSM Graph

Builds the full GSM scientific result from the image and current ST1
configuration.

The calculated result contains Green levels 1 through 255 and the associated
GSM variables.

## Reset

Resets the current Explorer interactive and presentation state for the loaded
image.

## Image path

Displays the path of the currently loaded image.

## Settings

Opens or closes the Explorer settings area.

Settings include:

- ST1;
- HSV;
- Custom ST1;
- ST3;
- processed-image background;
- Reset Settings.

## Export

Exports the current Explorer analysis after image processing and GSM graph
construction are available.

---

# 21. Explorer settings

## ST1

Available methods:

```text
G>R
G>R&G>B
2G-R-B>0
HSV
CUSTOM
```

The default method is:

```text
G>R
```

## HSV

HSV is available when HSV is the selected ST1 method.

Defaults:

```text
H min = 25
H max = 95

S min = 40
S max = 255

V min = 30
V max = 255
```

These values define three ranges rather than three individual threshold
values.

## Custom ST1

Select a Python file implementing:

```python
create_mask(image)
```

## ST3

Defaults:

```text
P = 50
m = 12
```

## Processed-image background

Default:

```text
Purple (150, 0, 150)
```

A custom RGB background can also be selected.

## Reset Settings

Restores the configured default values for:

- ST1;
- HSV ranges;
- ST3;
- Custom ST1;
- processed-image background.

---

# 22. Applying ST1 in Explorer

The Explorer deliberately separates ST1 from GSM graph construction.

The intended order is:

```text
Open Image
     ↓
Apply ST1
     ↓
Inspect segmentation
     ↓
Build GSM Graph
```

The processed image begins with the selected background and shows vegetation
according to the ST1 mask.

Scientific processing is performed using the original full-resolution RGB
image.

The displayed image may be resized to fit the screen, but the resized display
does not become the scientific input.

---

# 23. Building the GSM graph

After ST1 has been successfully applied, select:

```text
Build GSM Graph
```

The application calculates the GSM result for Green levels:

```text
1 ... 255
```

Once the result is available, Explorer provides access to:

- the Red GSM curve;
- the Blue GSM curve;
- the Green reference coordinate;
- numerical GSM values;
- ST3 information;
- optional fitted curves;
- interactive range selection.

The complete GSM result remains available even when the user subsequently
filters the visible Green range.

---

# 24. Interactive Green-range selection

Explorer provides synchronized Green-range controls.

A selected interval can be expressed as:

```text
27 ≤ Green ≤ 178
```

The selected range is reflected simultaneously in:

- the displayed image;
- the GSM graph.

The graph highlights the selected Green-level interval.

The image shows the vegetation corresponding to the current selection state.

The interactive selection is a filtering operation on the already calculated
GSM result.

The underlying complete 255-level GSM arrays are not recalculated merely because
the user changes the interactive range.

However, the **selected analysis is a different analysis** from the
full-range analysis.

In particular, fitting uses the data corresponding to the current selected
range when a selected-range fit is requested.

Therefore:

```text
Full-range fit
        ≠
Selected-range fit
```

when the selected range is only part of the complete GSM graph.

For example:

```text
Fit over Green = 1 ... 255
```

and:

```text
Fit over Green = 50 ... 170
```

can produce different:

```text
R²
RMSE
a
b
```

values.

The exported fit coefficients and fit statistics therefore refer to the
selected analysis represented by the current Green range and Reverse state.

---

# 25. Reverse selection

The Explorer **Reverse** option changes the selected Green range to its
complement.

For example, if:

```text
27 ≤ Green ≤ 178
```

is selected normally, Reverse selects:

```text
Green < 27
or
Green > 178
```

The effect is reflected in:

- the image;
- the graph;
- the exported selection state.

Reverse does not recompute the underlying complete 1–255 GSM arrays.

However, Reverse changes the selected data used by the Explorer analysis.

Consequently, it can change:

- the selected image;
- the highlighted graph region;
- the fitting data;
- fitted coefficients;
- fit statistics;
- exported analysis information.

Therefore:

```text
Normal selected-range fit
        ≠
Reverse selected-range fit
```

in general.

The `Selected` field in the exported Explorer CSV records the current
selection for each Green level.

---

# 26. GSM graph controls and interpretation

The Explorer graph displays the GSM observations as individual points.

The principal graph variables are:

```text
Red
Green
Blue
```

The Green sequence is the horizontal reference.

The Red and Blue data are the mean-channel values associated with each Green
level.

The graph may additionally show:

- selected Green-range shading;
- ST3 boundary markers;
- ST3 labels;
- fitted curves;
- cursor details.

Screen zoom and pan are presentation operations.

They do not change the underlying scientific data.

The vector PDF export represents the full scientific Green range:

```text
1 ... 255
```

regardless of on-screen zoom.

---

# 27. ST3 markers and labels

Explorer can display ST3 information visually.

Enable:

```text
Show ST3
```

to display the ST3 boundary information on the graph.

The markers identify the end points of the visible Red-ST3 and Blue-ST3
regions.

Enable:

```text
Show ST3 labels
```

to display the corresponding Green-level number beside the marker.

The labels contain the Green-level number and do not change the scientific
data.

ST3 visibility and labels are presentation options.

Changing ST3 parameters changes the ST3 classification itself.

---

# 28. Optional curve fitting

The GSM reference fitting model is:

```text
y = a · exp(b · G)
```

Separate exponential fits are available for:

```text
Red
Blue
```

The associated statistics are:

- R²;
- RMSE;
- coefficient `a`;
- coefficient `b`.

## Exponential (GSM reference)

This is the principal GSM exponential fitting model.

For a full-range analysis, the fit describes the available GSM data over the
full selected analysis range.

For a partial-range Explorer analysis, the fit describes only the selected
Green-level data.

## Polynomial degree 2 (Explorer extension)

Explorer also provides:

```text
Polynomial degree 2 (Explorer extension)
```

This is an exploratory application-level extension.

It is not presented as part of the historical GSM reference method.

Scientific publications should distinguish clearly between:

```text
GSM reference exponential fit
```

and:

```text
Explorer polynomial extension
```

### Interpretation of exported fit values

When the user selects only part of the GSM graph and exports the analysis, the
fitted coefficients and fit statistics in the exported result refer only to
the selected data.

They do not represent a fit to the full GSM graph.

For example:

```text
Fit over Green = 1 ... 255
```

and:

```text
Fit over Green = 27 ... 178
```

are different analyses and can have different:

```text
R²
RMSE
a
b
```

values.

The selected Green range and Reverse state should therefore always be recorded
and considered when interpreting fitted parameters.

---

# 29. Zoom, pan, and cursor inspection

Explorer provides independent presentation controls for the image and graph.

## Image zoom

Available controls include:

```text
Ctrl + Mouse Wheel — cursor-centered zoom
+                  — zoom in
-                  — zoom out
0                  — reset zoom
Middle mouse drag  — pan
Right-click + Arrow keys — pan
```

Image zoom does not modify the scientific image array.

## Graph zoom

Available controls include:

```text
Ctrl + Mouse Wheel — cursor-centered zoom
+                  — zoom in
-                  — zoom out
0                  — reset zoom
Middle mouse drag  — pan
Right-click + Arrow keys — pan
```

Graph zoom does not change:

- GSM values;
- ST3;
- fitting;
- Green-range selection;
- CSV output;
- PDF scientific range.

## Cursor details

When:

```text
Show cursor details
```

is enabled, moving the pointer over the graph can display the nearest Green
level together with associated values such as:

```text
Green
Red
Blue
dR/dG
dB/dG
Red-ST3
Blue-ST3
```

This is an inspection tool for reading the graph numerically.

---

# 30. Explorer export

The Explorer **Export** action creates a complete export set representing the
current analysis state.

The current state can include:

- loaded image;
- ST1 method;
- ST1 result;
- Green-range minimum;
- Green-range maximum;
- Reverse;
- fit state;
- fit model;
- analysis/display options.

The exported segmentation image is generated from the original full-resolution
image data and the selected mask.

It is **not a screenshot**.

The resulting PNG therefore retains the original image dimensions.

The exported GSM graph is a vector PDF.

The exported CSV contains the GSM result together with a separate:

```text
Selected
```

field.

The exported analysis also includes:

```text
Analysis.txt
```

which records the analytical configuration in human-readable form.

When fitting is enabled, the exported fitting values correspond to the data
used for the current Explorer analysis. For a partial Green-range selection,
the coefficients and fit statistics therefore describe that selected portion
rather than the full graph.

---

# 31. Explorer output files

For an input image with filename stem `<stem>`, Explorer uses:

```text
Explorer_<stem>_Segmented_G<min>-<max>.png
```

When Reverse is active:

```text
Explorer_<stem>_Segmented_G<min>-<max>_Reverse.png
```

The other outputs are:

```text
Explorer_<stem>_GSM_Graph.pdf
Explorer_<stem>_GSM_Results.csv
Explorer_<stem>_Analysis.txt
```

For example:

```text
Explorer_Sample 1_Segmented_G27-178.png
Explorer_Sample 1_GSM_Graph.pdf
Explorer_Sample 1_GSM_Results.csv
Explorer_Sample 1_Analysis.txt
```

The Explorer CSV contains:

```text
22 scientific GSM columns
+
Selected
```

The `Selected` field records whether each Green level belongs to the current
selected set.

The analysis record contains the current settings, Green range, Reverse state,
fit state, fit model, and related analysis information.

---

# 32. Background color

The default processed-image background is:

```text
RGB (150, 0, 150)
```

shown in the interface as:

```text
Purple (150, 0, 150)
```

The background is a display/export parameter.

It does not change:

- ST1 classification;
- ST2 numerical GSM values;
- ST3 classifications;
- exponential fitting.

Changing the background therefore changes the appearance of the processed
image without changing the GSM scientific calculation.

---

# 33. Custom ST1 segmentation

Advanced users may provide a custom Python segmentation module.

The required function is:

```python
def create_mask(image):
    ...
    return mask
```

The `image` argument is the RGB image array.

The returned mask should have:

```text
same height
same width
Boolean or binary interpretation
```

A minimal example is:

```python
import numpy as np


def create_mask(image):
    red = image[:, :, 0]
    green = image[:, :, 1]
    blue = image[:, :, 2]

    return (
        (green > red)
        & (green > blue)
    )
```

A Custom ST1 algorithm is part of the scientific configuration of an analysis.

For reproducibility, retain:

- the Custom `.py` file;
- its parameters;
- the software version;
- the original images;
- the resulting numerical outputs.

Do not assume that a Custom rule is equivalent to:

```text
G>R
```

The external Python file is loaded as part of the analysis configuration; it is
not bundled into the standard Windows application package.

---

# 34. Reproducibility

For a reproducible GSM analysis, preserve more than a screenshot or graph.

At minimum, retain:

```text
Software version

Original input images

ST1 method

ST1 parameters

ST3 P and m

Processed-image background

Green-range selection, when Explorer is used

Reverse state, when Explorer is used

Fit model, when fitting is used

Exported CSV

Exported PDF

Analysis.txt / Batch log

Custom segmentation file, when applicable
```

For a batch experiment, also document:

- input dataset identity;
- acquisition date;
- image-acquisition conditions;
- camera model;
- camera settings when relevant;
- imaging geometry;
- experimental identifiers.

For an Explorer analysis, the Green-range and Reverse state are particularly
important because fitted parameters can depend on the selected data.

---

# 35. Scientific considerations

Canopy GSM uses RGB image information, so image acquisition is part of the
scientific context.

When possible, keep relevant acquisition conditions consistent across an
experimental collection, including:

- camera model;
- lens;
- camera height;
- view geometry;
- field of view;
- time of day;
- illumination;
- exposure;
- white balance;
- canopy orientation;
- image resolution;
- relevant background conditions.

A change in image-derived RGB behavior can arise from:

- biological differences;
- illumination;
- camera settings;
- camera spectral response;
- shadows;
- background;
- image geometry;
- environmental conditions.

The software cannot determine the cause of such changes automatically.

## Camera-to-camera comparisons

Different camera models can have different spectral sensitivities and
color-rendering characteristics.

For this reason, **direct quantitative comparison of GSM outputs, especially
GSM graph characteristics, should currently be restricted to images acquired
with the same camera model under sufficiently comparable imaging conditions**.

Images from different camera models should not simply be pooled or compared as
though the cameras had identical spectral responses.

When images from different camera models must be compared, an appropriate
camera harmonization, normalization, or cross-camera calibration procedure
should first be established for the specific study.

No such cross-camera harmonization or normalization procedure is established
by the present GSM study.

Therefore, cross-camera comparisons without an appropriate harmonization
procedure should not be interpreted as directly comparable GSM measurements.

## Green level and canopy shading

Grouping vegetation pixels by Green level is not merely a color histogram.

The GSM graph organizes the relative Red and Blue behavior of vegetation along a
Green-gradient coordinate.

This provides a structured way to investigate patterns associated with
different illumination and shading conditions inside the canopy.

## Missing Green levels

Not every image necessarily contains vegetation pixels at every Green level.

A Green level with no contributing vegetation pixels does not represent a
measured value of zero.

Corresponding numerical outputs may therefore be undefined or represented by
blank or NaN-like values depending on the output format.

Such values should be interpreted as undefined observations rather than zero
measurements.

---

# 36. Troubleshooting

## The image is rejected

Check that the image is:

```text
8-bit
3-channel
RGB
```

and that its extension is supported.

The software does not silently convert an unsuitable image.

## The graph is unavailable

Explorer requires:

```text
Open Image
    ↓
Apply ST1
    ↓
Build GSM Graph
```

The GSM graph cannot be built before ST1 has been successfully applied.

## The segmentation looks unexpected

Check the selected ST1 method and its parameters.

Remember that:

```text
G>R
```

is the default method.

HSV is an optional segmentation method and uses ranges for H, S, and V.

## The image is purple or partly purple

Purple represents the selected processed-image background.

A purple region can therefore be correct.

Inspect the ST1 segmentation and, in Explorer, the current Green-range
selection before assuming that a purple region indicates an error.

## CSV values are blank

A blank or undefined value can be legitimate.

For example, a Green level containing no contributing vegetation pixels cannot
have a meaningful mean Red or mean Blue value.

## ST3 markers are not visible

Enable:

```text
Show ST3
```

ST3 labels additionally require:

```text
Show ST3 labels
```

## ST3 results seem unusual

ST3 is sensitive to the shape of the GSM curves and to canopy and imaging
conditions.

Check:

```text
P
m
```

and consider the biological and imaging context.

## A selected-range fit differs from a full-range fit

This is expected.

A fit over:

```text
1 ... 255
```

and a fit over:

```text
27 ... 178
```

are different analyses.

The coefficients and fit statistics are therefore not expected to be
identical.

## Results differ between two analyses

Check:

1. software version;
2. exact input images;
3. image channel and depth;
4. ST1 method;
5. ST1 parameters;
6. ST3 parameters;
7. Custom ST1 module;
8. Explorer Green range;
9. Reverse state;
10. fit model.

Do not use screenshots as the sole basis for scientific comparison.

---

# 37. Project structure

The public Python project is organized into scientific, application, and
resource components.

A typical repository structure is:

```text
Canopy-GSM-Python/
│
├── canopy_gsm.py
├── gui.py
├── batch_gui.py
├── batch_processor.py
├── explorer_gui.py
│
├── gsm_engine.py
├── st3.py
├── curve_fitting.py
├── io_utils.py
│
├── CanopyGSM.spec
├── CanopyGSM.png
├── CanopyGSM.ico
├── LICENSE
├── CITATION.cff
├── README.md
│
└── Data/
    └── Sample_Data/
        ├── Sample 1.jpg
        ├── Sample 2.jpg
        └── Sample 3.jpg
```

## `canopy_gsm.py`

Application entry point.

It creates the Qt application, displays the splash screen, and starts the main
window.

## `gui.py`

Main application shell, Launcher, navigation, branding, and common GUI
structure.

## `batch_gui.py`

Batch Processing user interface.

## `batch_processor.py`

Batch processing application layer, output generation, logging, and graph
export.

## `explorer_gui.py`

Canopy GSM Explorer interface, interactive Green-range selection, graph
presentation, fitting, zoom/pan, cursor inspection, and export.

## `gsm_engine.py`

Scientific GSM calculation engine.

## `st3.py`

ST3 curve-segmentation and classification implementation.

## `curve_fitting.py`

Exponential GSM curve-fitting implementation.

## `io_utils.py`

Strict RGB uint8 image input/output handling.

## `CanopyGSM.spec`

PyInstaller build specification for the Windows application package.

## `Data/Sample_Data/`

Public demonstration images for trying the software.

The sample images are included for demonstration and initial testing.

---

# 38. Historical MATLAB implementation

The historical Canopy GSM implementation is publicly available at:

https://github.com/haqueshenas/Canopy-GSM

The historical repository identifies the software as:

```text
Canopy GSM
Version 2.1
```

It contains the earlier MATLAB implementation and its principal components,
including:

```text
ST1.m
ST3.m
ExpFitting.m
ChangeBackColor.m
main.m
```

The historical Code Ocean resource is:

https://codeocean.com/capsule/1652693/tree/v2

The historical implementation is useful for understanding the origin and
scientific development of GSM.

It should be regarded as the historical software line and scientific reference,
whereas this repository contains the independent Python software line:

```text
Canopy GSM for Python
Version 1.0.0
```

---

# 39. Citation

## Scientific methodology

When using the GSM methodology in scientific work, cite the original article:

> Haghshenas, A., & Emam, Y. (2020).  
> *Green-gradient based canopy segmentation: A multipurpose image mining model
> with potential use in crop phenotyping and canopy studies.*  
> Computers and Electronics in Agriculture, 178, 105740.

DOI:

https://doi.org/10.1016/j.compag.2020.105740

## Python software

When the Python software itself is used, also cite the **specific software
release**.

For this release:

```text
Canopy GSM for Python
Version 1.0.0
```

Software DOI:

[https://doi.org/10.5281/zenodo.23134465](https://doi.org/10.5281/zenodo.23134465)

A software citation should identify both:

```text
Canopy GSM for Python
Version 1.0.0
```

and the original GSM scientific article when the GSM methodology is being used.

### APA-style software citation

Haghshenas, A. (2026). *Canopy GSM for Python* (Version 1.0.0) [Computer software]. Zenodo. [https://doi.org/10.5281/zenodo.23134465](https://doi.org/10.5281/zenodo.23134465)

---

# 40. Authors, development, and license

## Scientific concept and methodological direction

**Abbas Haghshenas**

Easy-Phenotyping Lab (EPL)

https://haqueshenas.github.io/EPL/

## Historical Canopy GSM work

The historical GSM work and earlier implementation are associated with:

- Abbas Haghshenas;
- Yahya Emam;
- Saeid Jafarizadeh.

The scientific publication identifies Abbas Haghshenas and Yahya Emam as the
authors of the GSM methodology. Saeid Jafarizadeh is acknowledged for his
contribution to writing the MATLAB codes for the earlier implementation.

## Current Python development

The scientific concept, methodological decisions, project direction, and
overall development of the Python project are led by **Abbas Haghshenas**.

The Python software has been developed with coding assistance from
**OpenAI GPT-5.6 Luna**.

AI assistance is a software-development aid and does not constitute scientific
authorship of the GSM methodology.

## License

Canopy GSM for Python is released under the MIT License.

The complete license text is reproduced below.

```text
MIT License

Copyright (c) 2026 Abbas Haghshenas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

A copy of the MIT License is also provided in the repository as:

```text
LICENSE
```

---

# 41. Frequently asked questions

## Is Canopy GSM free?

Yes.

Canopy GSM for Python is free and open-source software released under the MIT
License.

## Do I need MATLAB?

No.

The Python application is an independent software implementation.

The historical MATLAB implementation is provided as a historical scientific
reference.

## Do I need Python?

No, not when using the packaged Windows application.

Python and the project dependencies are required when running the source code
directly.

## What is the default ST1 method?

The default method is:

```text
G>R
```

It is not HSV.

## Is HSV a single threshold?

No.

HSV uses three ranges:

```text
H min – H max
S min – S max
V min – V max
```

A pixel must satisfy all three ranges.

## Can I use a grayscale image?

No.

The input must be a genuine:

```text
8-bit
3-channel
RGB
```

image.

## Can the software silently convert my image?

No.

Unsupported images are rejected rather than silently converted.

## Does changing ST1 change the GSM result?

Yes.

ST1 determines the vegetation mask.

Changing the mask changes which pixels enter the GSM calculation and can
therefore change downstream GSM values.

## Does changing the Green range change the scientific GSM result?

The underlying complete 1–255 GSM arrays are not recalculated merely because
the Explorer selection changes.

However, the **selected Explorer analysis does change**.

The selected image and graph can change, and any fitting performed on the
selected data can also change.

Therefore, a selected-range analysis must not be treated as numerically
identical to a full-range analysis.

## Does Reverse change the GSM calculation?

Reverse does not recompute the complete underlying GSM arrays.

It changes which part of those existing results is selected for Explorer
analysis.

Consequently, Reverse can change the selected image, selected graph region,
fitting data, fit coefficients, and fit statistics.

## Does zoom change scientific values?

No.

Zoom and pan are presentation operations.

## Does ST3 change the GSM curve?

Changing ST3 parameters changes ST3 classifications.

It does not change the upstream ST2 Red and Blue GSM curve values.

## Is ST3 universally interpretable as biological light classes?

No.

ST3 is an image-derived curve classification and can depend on canopy,
illumination, phenology, image characteristics, and experimental conditions.

Its classes should therefore be interpreted within the context of the
particular study.

## Is the polynomial fit part of the original GSM method?

No.

The Explorer degree-2 polynomial fit is explicitly an:

```text
Explorer extension
```

The GSM reference fitting model is exponential.

## Is Explorer only a preview?

No.

Explorer is an interactive analytical workspace.

It supports:

- Green-range selection;
- Reverse selection;
- dynamic image filtering;
- graph highlighting;
- ST3 inspection;
- optional fitting;
- cursor inspection;
- zoom and pan;
- complete export.

## Does the exported Explorer image come from a screenshot?

No.

The exported segmentation image is generated from the original full-resolution
image data and the selected mask.

## Can I export a selected part of the GSM graph?

Yes.

Explorer can export the current selected analysis.

When fitting is enabled, the exported coefficients and fit statistics refer to
the data used for the selected analysis.

A partial Green-range fit should therefore not be interpreted as a full-graph
fit.

## Can I process many images?

Yes.

Use Batch Processing for consistent processing of an image collection.

## Can I write my own ST1 segmentation algorithm?

Yes.

Use the Custom ST1 option and provide a Python file containing:

```python
create_mask(image)
```

The function should return a Boolean or binary mask with the same image height
and width.

Preserve the Custom module as part of the scientific record.

## Can I write my own ST3 algorithm?

The current release does not provide a GUI-based Custom ST3 plug-in mechanism.

An alternative ST3 method can be developed at source-code level through:

```text
st3.py
```

Such an alternative is a source-code modification rather than a documented
plug-in interface.

For reproducibility, preserve the modified ST3 code, its parameters, the
software version, the input data, and the resulting outputs.

## Where should I begin?

For a first analysis:

```text
Launch Canopy GSM
       ↓
Batch Processing or Explorer
       ↓
Open/select image(s)
       ↓
Choose ST1
       ↓
Inspect segmentation
       ↓
Build GSM graph / Start processing
       ↓
Inspect numerical and graphical outputs
```

For a scientific experiment, establish a consistent image-acquisition protocol
before analyzing the full dataset and document the software version and
analysis settings.

---

## Scientific-use note

Canopy GSM is designed to make quantitative RGB canopy image analysis more
accessible, transparent, and reproducible.

The software should be used as part of a scientific workflow rather than as an
automatic substitute for experimental judgment.

For publishable research, preserve the original images, image-acquisition
information, software version, analysis settings, outputs, and any custom
segmentation code.

---

<div align="center">

<img src="CanopyGSM.png" alt="Canopy GSM logo" width="90">

<br>

<strong>Canopy GSM for Python · Version 1.0.0</strong>

<br>

Green-gradient based canopy segmentation for quantitative crop-canopy image analysis

<br>

<a href="https://doi.org/10.5281/zenodo.23134465">
<img src="https://zenodo.org/badge/DOI/10.5281/zenodo.23134465.svg" alt="DOI">
</a>

<br><br>

<a href="https://haqueshenas.github.io/EPL/">
Easy-Phenotyping Lab (EPL)
</a>

<br><br>

Copyright © 2026 Abbas Haghshenas · MIT License

</div>
