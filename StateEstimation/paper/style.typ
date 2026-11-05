// Document-wide typography, page layout and metadata.
#let paper-style(body) = {
  set document(
    title: "Noise Sensitivity in Radar Ship Tracking: A Comparison of Linear and Nonlinear Kalman Filters",
    author: "Mattia Sicoli",
  )
  set page(
    paper: "a4",
    margin: (x: 18mm, top: 19mm, bottom: 18mm),
    numbering: "1",
    header: align(right, text(size: 8pt, fill: rgb("666666"))[Estimation and Filtering | Working draft]),
  )
  set text(font: "Libertinus Serif", size: 10pt, lang: "en")
  set par(justify: true, leading: 0.48em)
  set heading(numbering: "1.1")
  set math.equation(numbering: "(1)")
  set figure(gap: 5pt)
  show heading: set block(above: 1.05em, below: 0.55em)
  show figure.caption: set text(size: 8.7pt)
  show link: set text(fill: rgb("233c59"))

  body
}
