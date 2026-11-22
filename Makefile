.PHONY: install test simulate eeg benchmark dashboard ros-build

install:
	python -m pip install -e ".[all]"

test:
	ruff format --check .
	ruff check .
	pytest -q --cov=neurosafe --cov-report=term-missing --cov-fail-under=85

simulate:
	neurosafe simulate --trials 2000 --seed 42
	neurosafe sweep --trials 2000 --seed 42

eeg:
	neurosafe evaluate-eeg --subjects 1-10 --data-dir .cache/mne

benchmark:
	neurosafe benchmark-eeg --subjects 1-10 --data-dir .cache/mne

dashboard:
	streamlit run app/dashboard.py

ros-build:
	cd ros2_ws && colcon build --symlink-install
