<p align="center">
  <img src="CanopyGSM.png" alt="Canopy GSM logo" width="220">
</p>

<h1 align="center">Canopy GSM for Python</h1>

<p align="center">
  <strong>Green-gradient based Canopy Segmentation Model for quantitative RGB canopy analysis</strong>
</p>

<p align="center">
  Version 1.0.0 · Free and open-source crop-phenotyping software
</p>

<p align="center">
  <a href="https://doi.org/10.1016/j.compag.2020.105740">Scientific paper</a>
  ·

  <a href="https://haqueshenas.github.io/EPL/">Easy-Phenotyping Lab (EPL)</a>
</p>

<p align="center">
  <em>A practical Python implementation of GSM for crop science, canopy studies, image mining, and plant phenotyping.</em>
</p>

---

## Contents

- [1. What is Canopy GSM?](#1-what-is-canopy-gsm)
- [2. Scientific basis](#2-scientific-basis)
- [3. From MATLAB to Python](#3-from-matlab-to-python)
- [4. What the GSM graph represents](#4-what-the-gsm-graph-represents)
- [5. Scientific workflow](#5-scientific-workflow)
- [6. Installation and distribution](#6-installation-and-distribution)
- [7. Input image requirements](#7-input-image-requirements)
- [8. Launching the application](#8-launching-the-application)
- [9. Launcher: choosing a workflow](#9-launcher-choosing-a-workflow)
- [10. Batch Processing](#10-batch-processing)
- [11. Batch Processing settings](#11-batch-processing-settings)
- [12. Batch Processing step-by-step procedure](#12-batch-processing-step-by-step-procedure)
- [13. Batch Processing outputs](#13-batch-processing-outputs)
- [14. Understanding the 22-column GSM result table](#14-understanding-the-22-column-gsm-result-table)
- [15. Aggregate Batch tables](#15-aggregate-batch-tables)
- [16. Batch logging and validation](#16-batch-logging-and-validation)
- [17. Canopy GSM Explorer](#17-canopy-gsm-explorer)
- [18. Explorer toolbar: every button explained](#18-explorer-toolbar-every-button-explained)
- [19. Explorer settings](#19-explorer-settings)
- [20. Applying ST1 in Explorer](#20-applying-st1-in-explorer)
- [21. Building the GSM graph](#21-building-the-gsm-graph)
- [22. Interactive Green-range selection](#22-interactive-green-range-selection)
- [23. Reverse selection](#23-reverse-selection)
- [24. GSM graph controls and interpretation](#24-gsm-graph-controls-and-interpretation)
- [25. ST3 markers and labels](#25-st3-markers-and-labels)
- [26. Optional curve fitting](#26-optional-curve-fitting)
- [27. Zoom, pan, and cursor inspection](#27-zoom-pan-and-cursor-inspection)
- [28. Explorer export](#28-explorer-export)
- [29. Explorer output files](#29-explorer-output-files)
- [30. Background color](#30-background-color)
- [31. Custom ST1 segmentation](#31-custom-st1-segmentation)
- [32. Reproducibility](#32-reproducibility)
- [33. Scientific considerations](#33-scientific-considerations)
- [34. Troubleshooting](#34-troubleshooting)
- [35. Validation against MATLAB v2.1](#35-validation-against-matlab-v21)
- [36. Project structure](#36-project-structure)
- [37. Historical MATLAB implementation](#37-historical-matlab-implementation)
- [38. Citation](#38-citation)
- [39. Authors, development, and license](#39-authors-development-and-license)
- [40. Frequently asked questions](#40-frequently-asked-questions)

---

# 1. What is Canopy GSM?

**Canopy GSM for Python** is a research-oriented image-analysis application built around the **Green-gradient based Canopy Segmentation Model (GSM)**.

GSM was developed to extract quantitative information from ordinary RGB images of crop canopies. Instead of treating a canopy photograph only as a picture, GSM uses the image's RGB pixels as a structured numerical dataset.

The central idea is simple:

1. identify vegetation pixels;
2. classify those vegetation pixels according to their green intensity;
3. calculate the mean red and mean blue values associated with each green level;
4. plot those values against the green level;
5. use the resulting GSM graph and its derived numerical features to characterize canopy structure and shading-related patterns.

The scientific paper describes GSM as an image-mining technique based on relative variations in RGB triplets under different illumination conditions. Vegetation pixels are categorized into up to **255 groups according to their green level**, after which the mean red and mean blue values of each group are calculated and plotted against the green level. The resulting graph can be used for canopy identification and characterization, classification of canopy pixels according to degree of sunlight exposure, and generation of quantitative variables for phenotyping and data-mining analyses.

Canopy GSM for Python is intended for researchers working in areas such as:

- crop science;
- agronomy;
- crop production;
- plant physiology;
- plant breeding;
- crop phenotyping;
- canopy studies;
- image-based phenotyping;
- image mining;
- analysis of environmental or management effects on crop canopies.

The software is designed to be useful both for **ordinary end users**, who simply need to process images, and for **researchers who need transparent numerical outputs and reproducible workflows**.

---

# 2. Scientific basis

The underlying GSM methodology is described in:

> Haghshenas, A., & Emam, Y. (2020). *Green-gradient based canopy segmentation: A multipurpose image mining model with potential use in crop phenotyping and canopy studies.* Computers and Electronics in Agriculture, 178, 105740.

**DOI:** https://doi.org/10.1016/j.compag.2020.105740

The article describes how vegetation pixels in ground-based nadir RGB images can be categorized by green level and how the mean red and blue values associated with those green levels form two characteristic curves.

The published study reports that the resulting GSM graph can support several kinds of analysis, including:

- identifying and characterizing canopies using one or two equations;
- classifying canopy pixels according to their degree of exposure to sunlight;
- generating quantitative outputs for data mining and high-throughput phenotyping;
- deriving information that can be related to canopy coverage, NDVI, canopy temperature, environmental conditions, irrigation, and other experimental variables.

GSM should therefore be understood as an **image-derived quantitative characterization framework**. The software does not directly measure every biological variable in an experiment. It extracts structured image information that can be used alongside conventional phenotyping and other measurements.

For scientific interpretation, the original experimental context always remains important.

---

# 3. From MATLAB to Python

The historical Canopy GSM software was distributed as a MATLAB implementation and later as **Version 2.1**.

Historical resources:

- Code Ocean: https://codeocean.com/capsule/1652693/tree/v2
- Historical GitHub repository: https://github.com/haqueshenas/Canopy-GSM

The historical GitHub repository identifies the MATLAB implementation as **Canopy GSM Version 2.1** and documents the original workflow, including ST1, GSM graph generation, ST3, exponential fitting, individual result tables, and aggregate GSM tables.

The present software is deliberately called:

**Canopy GSM for Python — Version 1.0.0**

It is a **new Python software line**, not "MATLAB Version 3".

The relationship is therefore:

```text
Historical MATLAB Canopy GSM
        Version 2.1
              │
              ▼
   scientific reference path
              │
              ▼
   Canopy GSM for Python
        Version 1.0.0
```

The Python implementation keeps the established scientific calculation path as its reference while providing a modern Windows-oriented graphical application.

The Python application also adds functionality at the application and interaction layers, especially:

- a unified Launcher;
- Batch Processing;
- Canopy GSM Explorer;
- live processed-image visualization;
- interactive Green-range selection;
- Reverse selection;
- graph highlighting;
- optional interactive curve fitting;
- ST3 markers and labels;
- graph cursor readout;
- image and graph zoom;
- mouse/keyboard panning;
- vector PDF graph export;
- full-resolution PNG export;
- human-readable analysis records.

These application-layer extensions should not be confused with changes to the established GSM scientific definition.

---

# 4. What the GSM graph represents

A GSM graph uses the green level as its independent coordinate.

For each green level:

```text
G = 1, 2, 3, ... , 255
```

the vegetation pixels belonging to that green level are examined.

The scientific result contains, among other variables:

- mean red value;
- green level;
- mean blue value;
- red variance;
- blue variance;
- number of contributing pixels;
- red AUC;
- blue AUC;
- RB ABC;
- red slope;
- blue slope;
- red ST3 class;
- blue ST3 class;
- exponential fit statistics for red;
- exponential fit statistics for blue.

The two principal GSM curves are:

```text
Mean Red  versus Green level
Mean Blue  versus Green level
```

The green level provides the horizontal coordinate. The red and blue means provide the two image-derived responses.

The published GSM work reports two upward exponential-shaped curves, with the blue curve often showing a different degree of curvature from the red curve. Those patterns provide information about the canopy image and its shading-related distribution.

---

# 5. Scientific workflow

The complete Python application follows two complementary workflows.

## Batch Processing

```text
Folder of images
      │
      ▼
   ST1
      │
      ▼
GSM calculation
      │
      ├── ST2 numerical variables
      ├── ST3 classes
      └── exponential fitting
      │
      ▼
CSV tables + processed images + graphs + log
```

## Canopy GSM Explorer

```text
One image
   │
   ▼
Apply ST1
   │
   ▼
vegetation / background
   │
   ▼
Build GSM Graph
   │
   ▼
interactive Green-range selection
   │
   ├── image filtering
   ├── graph highlighting
   ├── Reverse selection
   ├── optional fitting
   └── cursor / ST3 inspection
   │
   ▼
Export
```

A central design principle is that the scientific calculation should have **one authoritative path**.

The GUI is a presentation and interaction layer around the scientific engine. It should not create a second independent GSM calculation that can silently disagree with the core engine.

In the Explorer, changing a Green range after the GSM result has been built does not recompute the complete GSM scientific result from scratch. Instead, the already-calculated result is filtered for interactive inspection.

---

# 6. Installation and distribution

Canopy GSM for Python is free and open-source software released under the MIT License.

The application is being prepared primarily for Windows desktop use.

The intended distribution model has two forms:

### Windows application package

A standalone Windows package can be distributed through the GitHub Releases section so that ordinary users do not need to install Python.

When a packaged release is provided, the package should be extracted as a complete application directory and launched through its application executable.

### Running from source

Researchers and developers may run the Python source directly.

The scientific and GUI components use standard scientific Python and Qt packages, including:

```text
Python
NumPy
SciPy
OpenCV
Matplotlib
PySide6
```

A validated development environment for the present project has used Python 3.13 together with current NumPy, SciPy, OpenCV, Matplotlib, and PySide6 releases available in the development environment.

For reproducible research, the exact dependency versions used for a particular software release should be recorded with that release.

---

# 7. Input image requirements

Canopy GSM for Python has a deliberately strict scientific input contract.

The application accepts:

- `.jpg`
- `.jpeg`
- `.png`
- `.tif`
- `.tiff`
- `.bmp`
- `.webp`

The image must be a **genuine 8-bit, 3-channel RGB image**.

This requirement is intentional.

The application does **not** make an unacceptable image acceptable by automatically converting it.

The following are rejected:

- grayscale images;
- RGBA / four-channel images;
- images with other channel counts;
- non-8-bit images;
- uint16 or other higher/lower-depth image arrays;
- Bayer or RAW data requiring demosaicing;
- HEIC / HEIF images.

In particular:

> A grayscale image is not converted to RGB merely to satisfy the interface.

> An RGBA image is not silently stripped to three channels.

> A uint16 image is not silently rescaled to uint8.

This strictness protects reproducibility because hidden conversions can change the pixel data that reaches the scientific algorithm.

The application may use OpenCV internally for file decoding, but the scientific engine works with the resulting RGB pixel array under the strict contract above.

---

# 8. Launching the application

The normal user experience is designed around a single application window.

The first screen is the **Canopy GSM Launcher**.

It provides three principal actions:

- **Batch Processing**
- **Canopy GSM Explorer**
- **About**

The Launcher itself remains a normal-sized window.

When a workflow is selected, the same application window switches to the selected workflow and becomes maximized.

The application window is also kept in the foreground so that it does not silently disappear behind unrelated applications.

---

# 9. Launcher: choosing a workflow

## Batch Processing

Choose **Batch Processing** when you need to process a collection of images using one consistent scientific configuration.

Typical use:

```text
hundreds of canopy images
        ↓
one segmentation configuration
        ↓
one batch run
        ↓
structured CSV tables
```

## Canopy GSM Explorer

Choose **Canopy GSM Explorer** when you want to inspect one image interactively.

Typical use:

```text
one interesting image
        ↓
visual inspection
        ↓
select Green range
        ↓
inspect graph
        ↓
inspect ST3
        ↓
optional fitting
        ↓
export
```

Explorer is intentionally a separate analytical workspace rather than Batch Processing with a few extra controls.

## About

The **About** dialog provides software identity, version information, scientific basis, historical MATLAB reference, authorship/development information, citation information, and license information.

The About dialog should not be confused with the scientific GSM workflow itself.

---

# 10. Batch Processing

Batch Processing is the high-throughput route.

Use it when the objective is to process many images under the same analysis settings and produce a reproducible collection of outputs.

The Batch interface is organized around:

1. input folder;
2. output folder;
3. scientific settings;
4. live processed-image visualization;
5. live GSM graph visualization;
6. processing controls;
7. status and logging.

The Batch visual workspace uses two principal panels:

- **Live Processed Image**
- **Live GSM Graph**

The graph display is intended to help the user understand what the scientific calculation is doing while the batch is running.

The GUI does not replace the scientific output tables. The CSV results remain the machine-readable numerical record.

---

# 11. Batch Processing settings

## ST1 segmentation method

The available ST1 methods are:

| Method | Rule | Purpose |
|---|---|---|
| `G>R` | `G > R` | Historical/default GSM-compatible rule |
| `G>R&G>B` | `G > R` and `G > B` | More restrictive RGB green selection |
| `2G-R-B>0` | `2G - R - B > 0` | Alternative RGB green-contrast rule |
| `HSV` | User-selected H/S/V thresholds | Adjustable color-space segmentation |
| `CUSTOM` | User-supplied Python mask function | Research-specific segmentation |

### `G>R`

This is the default historical-compatible segmentation rule:

```text
G > R
```

A pixel is included when its green component is greater than its red component.

### `G>R&G>B`

A pixel must satisfy both:

```text
G > R
G > B
```

This is more restrictive than `G>R`.

### `2G-R-B>0`

A pixel is included when:

```text
2G - R - B > 0
```

### HSV

The Python GUI exposes HSV thresholds as an extension to the original RGB rules.

Default values are:

```text
H: 25 – 95
S: 40 – 255
V: 30 – 255
```

OpenCV hue is represented on the 0–179 scale.

Changing the ST1 method or its parameters changes the vegetation mask. It can therefore change all downstream GSM variables.

### CUSTOM

A custom segmentation module may define:

```python
create_mask(image)
```

and return a boolean or compatible binary mask with the same height and width as the input image.

Custom algorithms are an extension mechanism. They are not part of the historical GSM definition.

---

# 12. Batch Processing step-by-step procedure

## Step 1 — Start the application

Launch Canopy GSM for Python.

## Step 2 — Open Batch Processing

Choose **Batch Processing** on the Launcher.

## Step 3 — Select the input folder

Choose the folder containing the supported RGB images.

For scientific work, it is good practice to keep all images in a collection acquired under comparable imaging conditions.

## Step 4 — Select the output folder

Choose the folder in which Canopy GSM should create its outputs.

## Step 5 — Review ST1

Choose the segmentation method.

For HSV, enter the desired thresholds.

For Custom, choose the segmentation `.py` file.

## Step 6 — Review ST3

The historical/default ST3 values are:

```text
P = 50
m = 12
```

ST3 is downstream of the main GSM curve construction.

Changing ST3 settings changes the ST3 classifications, but it does not redefine the upstream GSM values.

## Step 7 — Review the processed-image background

The default is:

```text
Purple (150, 0, 150)
```

The background affects visualization and exported processed-image appearance. It does not change the scientific RGB calculations.

## Step 8 — Inspect the live visualization

The live image and graph are for inspection of the current processing state.

The application deliberately does not use a resized preview as the scientific input.

## Step 9 — Start processing

Press:

**START PROCESSING**

The application processes images using the scientific GSM engine.

Long operations are handled outside the main GUI event path so that the interface can remain responsive.

## Step 10 — Review the outputs

After processing, inspect:

- individual result CSV files;
- aggregate GSM CSV files;
- processed images;
- GSM graphs;
- log file;
- scientific validation status.

---

# 13. Batch Processing outputs

The Batch workflow follows the historical Canopy GSM output organization while keeping the Python implementation explicit and reproducible.

For each image, the principal outputs are:

```text
Results of image <filename>.csv
Processed image output
Graphs of image <filename>.pdf
```

The exact filename extension of the processed-image file follows the current Python output implementation.

Three aggregate numerical tables are generated:

```text
Total GSM ST2.csv
Total GSM Num.csv
Total GSM Exp.csv
```

The purpose of the three aggregate tables is to make the 255-level GSM data and exponential fitting results easy to use in downstream data-mining workflows.

---

# 14. Understanding the 22-column GSM result table

Each individual GSM scientific result contains **22 columns**.

| # | Column | Meaning |
|---:|---|---|
| 1 | `Green_level` | Green level from 1 to 255 |
| 2 | `Mean_Red` | Mean red value at that green level |
| 3 | `Green` | Repeated green-level coordinate |
| 4 | `Mean_Blue` | Mean blue value at that green level |
| 5 | `Var_Red` | Red variance at that green level |
| 6 | `Var_Blue` | Blue variance at that green level |
| 7 | `Number_of_pixels` | Number of vegetation pixels contributing to that level |
| 8 | `Red_AUC` | Cumulative red-curve area value |
| 9 | `Blue_AUC` | Cumulative blue-curve area value |
| 10 | `RB_ABC` | Difference between the red and blue cumulative areas |
| 11 | `Red_Slope` | Local red-curve slope |
| 12 | `Blue_slope` | Local blue-curve slope |
| 13 | `Red_ST3_class` | ST3 class for the red curve |
| 14 | `Blue_ST3_class` | ST3 class for the blue curve |
| 15 | `R2_exp_Red` | R² of red exponential fit |
| 16 | `RMSE_exp_Red` | RMSE of red exponential fit |
| 17 | `exp_a_Red` | Red exponential coefficient `a` |
| 18 | `exp_b_Red` | Red exponential coefficient `b` |
| 19 | `R2_exp_Blue` | R² of blue exponential fit |
| 20 | `RMSE_exp_Blue` | RMSE of blue exponential fit |
| 21 | `exp_a_Blue` | Blue exponential coefficient `a` |
| 22 | `exp_b_Blue` | Blue exponential coefficient `b` |

The Python scientific result contains 255 Green-level rows.

For MATLAB-compatible individual result tables, the Python engine also supports a leading summary row containing the exponential-fit values followed by the 255 Green-level rows.

This is important when reproducing the historical file layout.

---

# 15. Aggregate Batch tables

## `Total GSM ST2.csv`

This table collects the red and blue GSM curve values for all images.

Its structure is:

```text
Image
R_G1 ... R_G255
B_G1 ... B_G255
```

There are therefore:

```text
1 + 255 + 255 = 511 columns
```

The first 255 curve values are the red GSM data.

The second 255 values are the blue GSM data.

This format is convenient for multivariate data analysis and machine-learning/data-mining workflows.

## `Total GSM Num.csv`

This table collects the number of pixels contributing to each green level.

Its structure is:

```text
Image
G1 ... G255
```

There are:

```text
1 + 255 = 256 columns
```

## `Total GSM Exp.csv`

This table collects the exponential fitting statistics for all processed images.

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

There are 9 columns.

This table is especially useful when the primary research question concerns image-to-image differences in the fitted GSM equations.

---

# 16. Batch logging and validation

Each Batch run should leave a machine-readable or human-readable record of the processing event.

Important information includes:

- software version;
- input folder;
- output folder;
- processing time/date;
- scientific settings;
- number of images;
- completed images;
- failed images, when any;
- error information;
- validation status.

The Python implementation also uses a compact scientific validation message when the generated CSV data agree with the established MATLAB v2.1 Golden Reference within the project's acceptance tolerances:

```text
SCIENTIFIC CSV RESULT: PASS
The Batch scientific CSV results agree with the frozen MATLAB v2.1 Golden Reference within the established acceptance tolerances.
```

This message is a validation result for the implementation; it is not a claim that every possible input image will produce scientifically perfect measurements.

---

# 17. Canopy GSM Explorer

The Explorer is a one-image analytical workspace.

It is designed for questions such as:

- What does ST1 select in this particular image?
- How does the GSM graph look?
- Which Green-level interval is of interest?
- What does the image look like after selecting that interval?
- Which red and blue curve values correspond to a particular Green level?
- Where are the ST3 boundaries?
- What happens when the selection is reversed?
- What does an exponential fit look like for the selected region?
- What does a second-degree polynomial extension look like?
- Can the exact selected analysis be exported?

Explorer is not intended to rerun the entire Batch workflow for one image.

Instead, it exposes the already-calculated GSM result as an interactive analysis object.

---

# 18. Explorer toolbar: every button explained

The main toolbar contains:

```text
Open Image
Apply ST1
Build GSM Graph
Reset
[image path]
Settings
Export
```

## Open Image

Opens one supported RGB image.

The input contract is the same strict RGB uint8 contract described earlier.

Opening a new image starts a fresh Explorer state.

## Apply ST1

Runs the selected segmentation method on the original full-resolution RGB image.

The output is displayed as a vegetation/background image.

A new ST1 application invalidates the previous GSM graph because the underlying vegetation mask has changed.

## Build GSM Graph

Builds the full GSM scientific result from the current image and ST1 configuration.

This includes the GSM Green-level calculations and downstream scientific outputs.

During the calculation, the graph panel displays:

**Please wait...**

This message is purely a user-interface indication that the scientific calculation is in progress.

## Reset

Returns the current Explorer selection and interactive display state to its initial state for the currently loaded image.

This includes:

- Green range;
- Reverse;
- visible GSM data;
- ST3 visibility;
- ST3 labels;
- fit visibility;
- fit model;
- image zoom;
- graph zoom.

It does not silently change the scientific core definition.

## Image path

Shows the currently selected image path.

It is informational and read-only.

## Settings

Opens or closes the collapsible settings area.

The settings area includes ST1, HSV, Custom ST1, ST3, background, and Reset Settings controls.

## Export

Exports the complete current Explorer analysis after ST1 and GSM graph construction are available.

The export contains:

- current selected image segmentation;
- vector GSM graph PDF;
- GSM CSV data;
- analysis text record.

---

# 19. Explorer settings

Explorer settings include four main categories.

## ST1 Segmentation

Choose one of:

```text
G>R
G>R&G>B
2G-R-B>0
HSV
CUSTOM
```

## HSV Thresholds

Available only when HSV is the active ST1 method.

Defaults:

```text
H min = 25
H max = 95
S min = 40
S max = 255
V min = 30
V max = 255
```

## Custom ST1

Choose a Python file implementing:

```python
create_mask(image)
```

## ST3

Defaults:

```text
P = 50
m = 12
```

## Processed Image Background

Default:

```text
Purple (150, 0, 150)
```

A custom RGB background can also be selected.

## Reset Settings

Restores:

- ST1 method;
- HSV thresholds;
- ST3 parameters;
- custom ST1 selection;
- processed-image background

to their configured defaults.

---

# 20. Applying ST1 in Explorer

The Explorer separates ST1 from GSM graph construction.

This is deliberate.

The intended sequence is:

```text
Open Image
     ↓
Apply ST1
     ↓
inspect the segmentation
     ↓
Build GSM Graph
```

The processed image begins with the selected background and reveals the vegetation according to the current ST1 mask.

The scientific processing itself is always performed on the original full-resolution image.

The displayed image may be resized for the user's screen, but the scientific engine does not use the resized preview to calculate the GSM result.

---

# 21. Building the GSM graph

After ST1 has been successfully applied, press:

**Build GSM Graph**

The program computes the GSM result for Green levels 1 through 255.

While the calculation is running:

```text
Please wait...
```

is displayed directly over the graph panel.

When the result is ready, the graph appears.

This design is especially useful on large images, where building the GSM result may take noticeable time.

Once the graph exists, the Explorer can perform interactive selections without repeating the complete GSM calculation.

---

# 22. Interactive Green-range selection

The Explorer provides two synchronized controls:

- a two-handle Green-range slider;
- minimum and maximum Green-level spin boxes.

A typical selection might be:

```text
27 ≤ Green ≤ 178
```

The selected interval is applied simultaneously to:

- the displayed image;
- the graph.

The graph highlights the selected Green-level region.

The image displays the corresponding selected vegetation according to the current selection state.

The selection is a **view/filtering operation on an existing scientific GSM result**.

It does not alter the stored 255-level GSM arrays.

The Export function records the selected state separately so that the interactive decision is reproducible.

---

# 23. Reverse selection

The **Reverse** checkbox inverts the current Green-range selection.

For example, if:

```text
27 ≤ Green ≤ 178
```

is selected normally, Reverse changes the selected set to:

```text
Green < 27
or
Green > 178
```

The current selection state is reflected in both:

- the image;
- the graph.

Reverse is an Explorer analysis/display operation.

It does not redefine or recompute the underlying GSM scientific arrays.

When an exported CSV is generated, the current selection is recorded in the `Selected` column.

---

# 24. GSM graph controls and interpretation

The Explorer graph is designed to remain readable while supporting detailed inspection.

The graph displays the GSM data points as separate points rather than forcing a connected visual curve through them.

The main channels are:

- Red;
- Green;
- Blue.

The Green sequence is the horizontal reference.

The Red and Blue data are the image-derived mean-channel observations associated with each Green level.

The graph may also display:

- selected Green-range shading;
- ST3 boundary markers;
- ST3 numeric labels;
- fitted curves;
- cursor/readout information.

The graph's screen zoom does not change the data.

The graph PDF is always exported at the full scientific Green range:

```text
1 ... 255
```

regardless of the on-screen zoom level.

---

# 25. ST3 markers and labels

ST3 is a secondary curve-segmentation/classification layer in the GSM workflow.

Default settings:

```text
P = 50
m = 12
```

The historical MATLAB documentation notes that ST3 classes can depend strongly on canopy condition and may be adjusted for a particular dataset.

The Explorer can display ST3 visually through:

**Show ST3**

This displays the last point of each visible Red-ST3 and Blue-ST3 region using open-circle markers.

The Explorer also provides:

**Show ST3 labels**

When enabled, the exact Green-level number is printed next to the visible ST3 marker.

The labels do not change the scientific data.

The same marker and label concept is available in the exported vector PDF.

Changing ST3 visibility changes only the presentation.

Changing ST3 parameters changes the ST3 classification result, but does not redefine the underlying ST2 GSM curve values.

---

# 26. Optional curve fitting

The scientific GSM reference fit uses an exponential model:

```text
y = a · exp(b · G)
```

Separate fits are performed for:

- the Red GSM curve;
- the Blue GSM curve.

The associated fit statistics include:

- R²;
- RMSE;
- coefficient `a`;
- coefficient `b`.

## Exponential (GSM reference)

This option uses the established GSM exponential fitting path.

When used for the full GSM result, the fit values correspond to the scientific output columns 15–22.

## Polynomial degree 2 (Explorer extension)

The Explorer also provides:

```text
Polynomial degree 2 (Explorer extension)
```

This is explicitly an **Explorer extension**.

It is not presented as part of the historical MATLAB GSM reference.

The purpose is exploratory comparison of the selected Green-range data with a second-degree polynomial representation.

For scientific publication, users should clearly distinguish:

```text
GSM reference exponential fit
```

from:

```text
Explorer polynomial extension
```

---

# 27. Zoom, pan, and cursor inspection

Explorer provides independent zoom for the image and graph.

## Image zoom

Controls:

- `Ctrl + Mouse Wheel` — cursor-centered zoom;
- `+` — zoom in;
- `-` — zoom out;
- `0` — reset zoom;
- middle-mouse drag — pan;
- right-click to focus the image, then Arrow keys — pan.

The image zoom never modifies the scientific image array.

## Graph zoom

Controls:

- `Ctrl + Mouse Wheel` over the graph plot — cursor-centered zoom;
- `+` — zoom in;
- `-` — zoom out;
- `0` — reset zoom;
- middle-mouse drag — pan;
- right-click to focus the graph, then Arrow keys — pan.

The graph zoom never changes:

- GSM result values;
- ST3;
- fitting;
- Green selection;
- CSV data;
- PDF export.

## Cursor details

When:

**Show cursor details**

is enabled, moving the pointer over the graph can show the nearest Green level together with the associated values, including:

- Green;
- Red;
- Blue;
- Red slope;
- Blue slope;
- Red-ST3;
- Blue-ST3.

This is a diagnostic and inspection tool for reading the graph precisely.

---

# 28. Explorer export

The Explorer **Export** button creates one complete export set.

The export is based on the current interactive state.

The current state includes:

- image;
- ST1 result;
- Green-range minimum;
- Green-range maximum;
- Reverse;
- optional fitting state;
- optional model choice;
- visibility settings.

The exported image is produced from the original full-resolution image array and the selected mask.

It is **not** a screenshot.

The exported image is therefore not limited by the size of the GUI window.

The exported graph is a vector PDF.

The exported CSV contains the full GSM result and a separate `Selected` field describing the interactive selection.

The `Analysis.txt` file records the analytical configuration in a human-readable form.

---

# 29. Explorer output files

For an image whose filename stem is `<stem>`, the Explorer uses:

```text
Explorer_<stem>_Segmented_G<min>-<max>.png
```

and, when Reverse is active:

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

The exported CSV contains:

```text
22 scientific GSM columns
+
Selected
```

The `Selected` field contains:

```text
Yes
No
```

for each Green level.

The analysis text record contains the current settings, selected range, Reverse state, visualization states, fit state, and fit information.

---

# 30. Background color

The default processed-image background is:

```text
RGB (150, 0, 150)
```

This purple background was selected to provide strong visual separation from common vegetation colors and remains compatible with the established MATLAB workflow.

The background is a **display/export parameter**.

It does not alter:

- ST1 classification;
- ST2 numerical values;
- ST3 numerical classes;
- exponential fitting.

Changing the background therefore changes the appearance of the derived image without changing the scientific GSM result.

---

# 31. Custom ST1 segmentation

Advanced users may provide a custom Python segmentation file.

The file should define:

```python
def create_mask(image):
    ...
    return mask
```

The function receives the RGB image array and should return a mask with:

```text
same height
same width
binary / Boolean interpretation
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

A Custom algorithm should be treated as part of the scientific configuration of an analysis.

For reproducibility, archive:

- the Custom `.py` file;
- the software version;
- its parameters;
- the original images;
- the output tables.

Do not assume that a Custom rule is equivalent to the historical GSM `G>R` rule.

---

# 32. Reproducibility

A reproducible analysis should preserve more than the final graph image.

At minimum, retain:

```text
Software version
Input images
ST1 method
ST1 parameters
ST3 P and m
Background setting
Green-range selection, when Explorer is used
Reverse state, when Explorer is used
Fit model, when fitting is used
Exported CSV
Exported PDF
Analysis.txt / log
Custom segmentation file, when applicable
```

For a batch experiment, also preserve:

- input folder identity;
- output folder identity;
- acquisition conditions;
- processing date;
- dataset identifiers;
- camera and imaging configuration when relevant.

This is especially important because RGB image-derived quantities can be affected by the image itself.

---

# 33. Scientific considerations

Canopy GSM is powerful partly because it uses inexpensive RGB imagery, but that also means the image-acquisition conditions matter.

When possible, keep the following consistent across an experimental collection:

- camera;
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
- background conditions.

A change in image-derived RGB behavior can reflect:

- biological change;
- illumination change;
- camera-setting change;
- shadows;
- background effects;
- image geometry;
- or another environmental factor.

The software cannot determine the cause automatically.

Therefore, GSM-derived variables should be interpreted as quantitative image traits and integrated with the experimental design.

### Green level and canopy shading

The purpose of sorting vegetation pixels by Green level is not simply to create a color histogram.

The GSM graph organizes the red and blue behavior of the selected vegetation pixels along a green-gradient axis.

This provides a structured way to inspect patterns associated with different levels of illumination or canopy shading.

### Missing Green levels

Not every image necessarily contains vegetation pixels at every Green level.

When a Green level contains no contributing vegetation pixels, corresponding values can be undefined.

In machine-readable output, undefined values may be represented as blank or NaN-like scientific values depending on the specific output representation.

Users should not interpret an undefined Green level as a measured zero.

---

# 34. Troubleshooting

## The image is rejected

Check that the file is:

```text
8-bit
3-channel
RGB
```

Do not rely on automatic conversion.

## The graph is unavailable

Explorer requires:

```text
Open Image
   ↓
Apply ST1
   ↓
Build GSM Graph
```

If ST1 has not been applied, the graph cannot be built.

## Build GSM Graph appears to pause

Large images can require noticeable processing time.

The graph panel displays:

```text
Please wait...
```

while the GSM scientific calculation is running.

Do not repeatedly press the button during processing.

## The image is visually purple or partially purple

This may be correct.

Purple represents the selected processed-image background.

Inspect the ST1 result and the selected Green range rather than assuming that every purple region indicates a failure.

## The image seems zoomed back to the beginning

Opening a new image or resetting Explorer intentionally resets image and graph zoom.

Changing an interactive selection, including Reverse, is not supposed to reset the image zoom.

## ST3 markers are missing

Check:

```text
Show ST3
```

ST3 labels also require:

```text
Show ST3 labels
```

## The ST3 result seems unusual

ST3 is a secondary classification layer and can depend on canopy condition.

The historical implementation allows the `P` and `m` settings to be adjusted for a particular dataset.

## CSV values are blank

Blank values can represent undefined quantities.

For example, a Green level with no contributing vegetation pixels has no meaningful mean red or mean blue value.

## Results differ from a previous run

Check, in order:

1. software version;
2. exact input files;
3. exact segmentation method;
4. ST1 parameters;
5. ST3 settings;
6. image format/channel/depth;
7. any Custom segmentation module;
8. Explorer selection and fit settings.

A scientific comparison should never begin by comparing screenshots alone.

---

# 35. Validation against MATLAB v2.1

The scientific Python core is maintained separately from the GUI.

The canonical scientific components are:

```text
gsm_engine.py
st3.py
curve_fitting.py
io_utils.py
```

The implementation has been validated against **actual MATLAB v2.1 Golden Reference outputs** for three sample images.

The validation compares the scientific result columns and accepts only the previously established numerical tolerances for the exponential-fitting fields.

The development validation result has shown:

```text
3 sample images
22 scientific columns
PASS
```

This validation is an internal implementation check against the frozen historical reference.

It does not imply that every image-acquisition scenario is biologically or experimentally optimal.

The Python implementation also keeps the scientific engine independent from the graphical presentation layer so that visual changes do not silently alter the core numerical path.

---

# 36. Project structure

The Python project is organized so that scientific code and user-interface code remain distinguishable.

A typical structure is:

```text
CanopyGSM/
│
├── main.py
├── gui.py
├── batch_gui.py
├── explorer_gui.py
│
├── gsm_engine.py
├── st3.py
├── curve_fitting.py
├── io_utils.py
│
├── CanopyGSM.png
├── CanopyGSM.ico
│
├── reference/
│   └── matlab_v2_1/
│
└── README.md
```

### `main.py`

Application entry point.

### `gui.py`

Main Launcher and workflow navigation.

### `batch_gui.py`

Batch Processing user interface and workflow orchestration.

### `explorer_gui.py`

Canopy GSM Explorer user interface, interactive filtering, graph presentation, fitting, zoom, and export.

### `gsm_engine.py`

Scientific GSM calculation engine.

### `st3.py`

ST3 reference algorithm.

### `curve_fitting.py`

Exponential curve-fitting implementation.

### `io_utils.py`

Strict RGB uint8 image input/output handling.

### `reference/matlab_v2_1/`

Historical MATLAB Golden Reference data and reference materials used during scientific validation.

---

# 37. Historical MATLAB implementation

The original Canopy GSM software was distributed as MATLAB code.

The historical GitHub repository:

https://github.com/haqueshenas/Canopy-GSM

identifies:

```text
Canopy GSM
Version 2.1
```

and includes the principal MATLAB components:

```text
ST1.m
ST3.m
ExpFitting.m
ChangeBackColor.m
main.m
```

The historical README documents:

- ST1;
- ST3;
- the 255 Green-level groups;
- the 22-column individual CSV output;
- `Total GSM Exp.csv`;
- `Total GSM ST2.csv`;
- `Total GSM Num.csv`;
- the historical purple processed-image convention.

The historical Code Ocean resource is:

https://codeocean.com/capsule/1652693/tree/v2

The original software should be treated as the historical scientific reference rather than as the current Python application's user interface.

---

# 38. Citation

When using the GSM methodology in scientific work, cite the original paper:

**Haghshenas, A., & Emam, Y. (2020).**  
*Green-gradient based canopy segmentation: A multipurpose image mining model with potential use in crop phenotyping and canopy studies.*  
Computers and Electronics in Agriculture, 178, 105740.  
https://doi.org/10.1016/j.compag.2020.105740

When the Python software itself is used, also cite the **specific software release** once its archival release DOI is available.

For reproducibility, it is good practice to record:

```text
Canopy GSM for Python
Version 1.0.0
```

together with the scientific paper citation.

---

# 39. Authors, development, and license

## Scientific concept and methodological direction

**Abbas Haghshenas**

Easy-Phenotyping Lab (EPL)

https://haqueshenas.github.io/EPL/

## Historical Canopy GSM software

The historical MATLAB Canopy GSM materials identify:

- Abbas Haghshenas
- Yahya Emam
- Saeid Jafarizadeh

as contributors/authors of the earlier implementation and associated work.

## Current Python development

The scientific concept, methodological decisions, project direction, and overall development of the Python project are led by **Abbas Haghshenas**.

The Python code has been developed with coding assistance from **OpenAI GPT-5.6 Luna**.

AI assistance is a software-development aid and does not constitute scientific authorship of the GSM methodology.

## License

Canopy GSM for Python is released under the:

**MIT License**

The license is intended to permit broad use, inspection, modification, and redistribution subject to the license terms.

---

# 40. Frequently asked questions

## Is Canopy GSM free?

Yes. The project is intended as free and open-source crop-phenotyping software.

## Do I need MATLAB to use Canopy GSM for Python?

No.

The Python application is an independent software implementation.

The historical MATLAB implementation is retained as a scientific/reference resource.

## Do I need Python?

For a packaged Windows application, no Python installation is intended to be necessary.

When using the source code directly, Python and the project dependencies are required.

## Can I use grayscale images?

No.

The application requires a genuine 8-bit, 3-channel RGB image.

## Can the software silently convert my image?

No.

Unsupported channel counts, grayscale images, and non-8-bit images are rejected rather than silently converted.

## Does changing the Green range change the scientific GSM result?

No.

Interactive Green-range selection filters the existing GSM result for Explorer analysis.

The full 1–255 scientific data remain available.

## Does Reverse change the GSM calculation?

No.

Reverse changes which part of the existing GSM result is selected for Explorer inspection.

## Does zoom change scientific values?

No.

Zoom is presentation-only.

## Does ST3 change the GSM curve?

ST3 is a downstream classification layer.

Changing ST3 settings changes the ST3 classifications, not the upstream ST2 GSM curve values.

## Is the polynomial fit part of the historical GSM method?

No.

The Explorer's degree-2 polynomial fit is explicitly labeled an **Explorer extension**.

The GSM reference fit is exponential.

## Is the Explorer just a preview?

No.

Explorer is an interactive analysis workspace.

It allows Green-range selection, Reverse selection, dynamic image and graph filtering, ST3 inspection, optional fitting, detailed cursor inspection, zoom/pan, and complete export.

## Does the exported Explorer image come from a screenshot?

No.

The exported image is generated from the original full-resolution image array and the current mask.

## Can I process hundreds of images?

Yes.

Use Batch Processing for repeated, consistent analysis across an image collection.

## Can I write my own segmentation algorithm?

Yes.

Advanced users can supply a Custom ST1 Python module defining:

```python
create_mask(image)
```

The Custom module should be preserved with the scientific record.

## Where should I begin?

For a new user:

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
Build / Start processing
      ↓
Inspect CSV and graph outputs
```

For a researcher beginning a new experiment, first establish a consistent image-acquisition protocol and then document the exact segmentation and software settings used for the analysis.

---

## A note on scientific use

Canopy GSM is designed to make quantitative RGB image analysis more accessible, transparent, and reproducible.

The software should be used as part of a scientific workflow rather than as an automatic substitute for experimental judgment.

For publishable research, preserve the original images, software version, settings, outputs, and relevant acquisition information.

---

<p align="center">
  <strong>Canopy GSM for Python · Version 1.0.0</strong><br>
  Green-gradient based canopy segmentation for quantitative crop-canopy image analysis
</p>

<p align="center">
  <a href="https://haqueshenas.github.io/EPL/">Easy-Phenotyping Lab (EPL)</a>
</p>

<p align="center">
  Copyright © 2026 Abbas Haghshenas · MIT License
</p>
