# Estimation and Filtering: Student Slides

A short graduate course on state estimation in discrete-time dynamic systems: from the
Kalman filter, through the extended Kalman filter, to sigma-point filters such as the
unscented and cubature Kalman filters, with worked comparisons on nonlinear models.

This repository holds the **presentation** used in class, the editor that assembles it,
and the small filter experiments behind its comparison charts.

## Presentation

The deck lives in `presentation/` and is made of three modules:

| Folder | Content | Slides |
| --- | --- | --- |
| `presentation/1` | From the Kalman filter to the UKF: sigma points, weights, reconstruction, limits | 15 |
| `presentation/2` | The square-root cubature Kalman filter: time and measurement updates, numerical differences | 6 |
| `presentation/3` | Four filters side by side on a nonlinear problem, and when linearization actually matters | 15 |

`presentation_editor.html` is the entry point: it reads the modules, numbers the slides
globally and plays the result as one deck.

## Using the editor

1. Open `presentation_editor.html` in Chrome or Edge.
2. Pick the `presentation` folder (the deck root, not a single module).

The editor discovers the subfolders by itself, in natural order (`1/`, `2/`, `3/`, ...),
and puts every slide in one sequence: the first slide of `2/` is number 16, and so on.
The counter in Present and in the list uses this global number, while inside each folder
the files stay numbered from `01`; the up/down buttons move a slide only within its own
module and renumber that folder.

The chosen folder is remembered: on reopening, the editor resumes it by itself; if the
browser asks for permission again, `Riprendi <name>` appears and one click is enough.

Each module (folder) has its own `slideui.css` and `slideui.js`: preview, Present and
Export inline the assets of the folder the slide belongs to, so two modules can use
different frameworks and styles in the same deck. If a folder has no assets of its own,
the editor walks up to the parent folders and finally to the default framework.

In Present, slides crossfade; `Esc` closes and `F` takes the app fullscreen (`F` again,
or `Esc`, to leave).

## Experiments

`experiments/filters_comparison/` contains the Python scripts and JSON results that
compare KF, EKF, UKF and CKF on the same nonlinear test case; the charts in the deck come
from these runs.
