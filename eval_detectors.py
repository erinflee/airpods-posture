"""
Evaluate pitch detectors on recorded CSVs -> tune config.py from results

  - load baseline.json
  - per labeled CSV, compare pitch_only_label and SmoothedPitchClassifier to truth
  - print accuracy for Baseline A and B
"""

