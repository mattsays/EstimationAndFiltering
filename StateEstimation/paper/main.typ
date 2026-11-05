// Entry point: shared style, paper sections, and bibliography.
#import "style.typ": paper-style
#show: paper-style

#include "sections/front-matter.typ"
#include "sections/introduction.typ"
#include "sections/models.typ"
#include "sections/methods.typ"
#include "sections/experiments.typ"
#include "sections/results.typ"
#include "sections/discussion.typ"
#include "sections/conclusion.typ"

#bibliography("references.bib", title: [References], style: "ieee")
