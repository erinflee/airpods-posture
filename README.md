# AirPods Posture

Headless Mac posture monitor: AirPods motion → temporal classifier → `osascript` notification.

## build order

1. `config.py` → `mac_motion.py` → `baseline.py` → `calibrate.py`
2. `./scripts/build_app.sh` then record with `record_mac.py`
3. `features.py` → `inspect_data.py` → `baselines.py` → `eval_baselines.py`
4. **Learn PyTorch:** `dataset.py` → `model.py` → `train.py`
5. `state_machine.py` → `notify.py` → `run_daemon.py`
