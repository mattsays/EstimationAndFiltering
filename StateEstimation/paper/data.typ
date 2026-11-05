// Shared experiment data, validation and table helpers.
#let data = json("../ship_tracking/noise-sensitivity.json")
#assert(data.complete, message: "Compile only after the experiments have completed.")
#assert(data.runs == 30 and data.scans == 800 and data.burn_in == 300 and data.seed == 20261026,
  message: "This draft describes 30 tracks, 800 scans, burn-in 300 and seed 20261026. Update the prose for a different protocol.")
#assert(data.dt == 0.01 and data.substeps == 5,
  message: "This draft describes dt=0.01 and five substeps per radar scan.")
#assert(data.base == (sigma_r: 0.01, sigma_b_deg: 0.5, q_position: 0.01, q_velocity: 0.01),
  message: "Update the paper's nominal noise settings for this dataset.")
#let expected-levels = (
  sigma_b_deg: (0.5, 2.0, 5.0, 10.0, 20.0, 30.0),
  sigma_r: (0.01, 0.02, 0.05, 0.1, 0.2, 0.5),
)
#assert(data.sweeps.keys().sorted() == expected-levels.keys().sorted(),
  message: "This paper includes only bearing and range noise sweeps.")
#for (parameter, expected) in expected-levels {
  assert(data.sweeps.at(parameter).map(case => case.value) == expected,
    message: "Update the paper's sweep grid for " + parameter)
}
#let methods = ("KF", "EKF", "UKF", "CKF", "SCKF")
#let names = (KF: "KF-CV", EKF: "EKF", UKF: "UKF", CKF: "CKF", SCKF: "SCKF")
#let nominal = data.sweeps.sigma_b_deg.first().methods
#let digits(value, places: 4) = str(calc.round(value, digits: places))
#let endpoint(parameter, method, metric) = data.sweeps.at(parameter).last().methods.at(method).at(metric)
#let nominal-table() = {
  let cells = ()
  for method in methods {
    let r = nominal.at(method)
    assert(r.status == "ok")
    cells.push(names.at(method))
    cells.push(digits(r.pos_rmse))
    cells.push(digits(r.vel_rmse))
    cells.push(digits(1000 * r.time_s_per_track, places: 1))
  }
  table(
    columns: (1.2fr, 1.4fr, 1.4fr, 1.4fr),
    align: (left, right, right, right),
    inset: (x: 7pt, y: 5pt),
    stroke: 0.35pt + rgb("cbd1d7"),
    fill: (x, y) => if y == 0 { rgb("eef1f4") } else { none },
    table.header([*Method*], [*Position (m)*], [*Velocity (m/s)*], [*Time (ms/track)*]),
    ..cells,
  )
}
