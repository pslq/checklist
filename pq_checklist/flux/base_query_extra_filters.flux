from(bucket: "<BUCKET>")
  |> range(start: <START_RANGE>, stop: <STOP_RANGE>)
  |> filter(fn: (r) => r["_measurement"] == "<MEASUREMENT>")
  <EXTRA_FILTERS>
  |> derivative(unit: 1s, nonNegative: true)
  |> yield(name: "<YIELD_FUNCTION>")
