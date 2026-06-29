# Contributing to UAP-Video-Detector

First off, thank you for taking the time to contribute! 🎉 

Projects like this thrive because of developers, data scientists, and researchers like you. Whether you are fixing a bug, optimizing a YOLO inference loop, or refining the Web UI, your help makes a massive difference in pushing open-source UAP research forward.

---

## 📬 Becoming an Active Contributor

If you want to become an **active core contributor** with write permissions to the repository, help manage the roadmap, or propose deep architectural changes, please reach out directly:

* **Core Maintainer:** Adriel Kirch
* **Contact Email:** [adriel.kirch.1@gmail.com](mailto:adriel.kirch.1@gmail.com)

Please send a brief note outlining your background, your experience with computer vision/Python, and what areas of the project (Inference, UI, Ingestion, or DevOps) you are most passionate about accelerating.

---

## 🛠️ How Can I Contribute?

### 1. Reporting Bugs & Suggesting Features
* Before opening a new issue, please search the **Issues** tab to see if it has already been reported.
* Use the provided **Issue Templates** to report bugs. Be sure to include your OS, Python version, hardware configuration (CUDA vs. CPU), and a minimal reproducible code snippet or video sample if applicable.

### 2. Conceptual & Philosophical Debates
* Because UAP data and AI tracking can spark speculative ideas, we request that all hardware setups, camera tracking mechanics, and philosophical brainstorms take place under the **GitHub Discussions** tab. 
* Keep the **Issues** tab strictly reserved for actionable code tasks, bugs, and feature implementations.

### 3. Submitting Code Changes (Pull Requests)
To keep the main codebase highly stable, please adhere to the following workflow:

1. **Fork the Repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/amazing-new-feature

---

## 🧪 Test-Driven Development (TDD) & Unit Testing Specification

To maintain a highly reliable computer vision pipeline, **this project strictly enforces a Test-Driven Development (TDD) approach.** Before writing or modifying any features in `src/`, you are expected to define the technical requirements via unit tests. 

Your Pull Request (PR) **will not be merged** unless it meets the detailed testing specifications below.

### 1. The Core Rule: Write the Test First
When implementing a new feature or fixing a bug:
1. **Write a failing test case** under the `tests/` directory that defines the expected behavior.
2. **Run the test suite** to ensure it fails for the right reason (`pytest`).
3. **Write the minimal code** in `src/` required to make that test pass.
4. **Refactor** the code for optimization and style, ensuring the tests stay green.

### 2. Strict Technical Requirements for Unit Tests

Every contribution must include matching unit tests that adhere to these strict constraints:

* **Zero Flakiness (Determinism):** Machine learning models can be unpredictable. However, your unit tests must be 100% deterministic. Mock out random initializations or floating-point variations if necessary.
* **Mocking Live Hardware & I/O:** * Do **not** run actual live video streams or capture hardware frames during tests. Mock your video capture inputs (`cv2.VideoCapture`) using sample mock frames or static arrays.
  * Do **not** download YOLO weights (`.pt` files) from the internet during a test run. Use small, local mock weights or mock the inference layer output entirely.
* **Code Coverage:** New logic must have at least **85% statement coverage**. Use `pytest-cov` locally to verify your coverage before pushing code.

### 3. Concrete Testing Examples

To keep the architecture clean, structure your tests using `pytest` to target specific layers:

#### Example A: Testing the Inference Layer (`src/inference/`)
If you write a component that filters out known objects based on a confidence threshold, your test must verify the exact filtering logic:

```python
import pytest
import numpy as np
from src.inference.filters import AnomalyFilter

def test_anomaly_filter_flags_low_confidence():
    """Ensure objects with confidence below the threshold are flagged as UAPs."""
    detector = AnomalyFilter(threshold=0.50)
    
    # Mock a high-confidence known object (Plane at 80% confidence)
    known_mock = {"class": "plane", "confidence": 0.80, "bbox": [100, 100, 50, 50]}
    # Mock a low-confidence unknown object (Anomaly at 30% confidence)
    uap_mock = {"class": "unknown", "confidence": 0.30, "bbox": [200, 200, 30, 30]}
    
    results = [known_mock, uap_mock]
    filtered_anomalies = detector.isolate_anomalies(results)
    
    assert len(filtered_anomalies) == 1
    assert filtered_anomalies[0]["confidence"] == 0.30