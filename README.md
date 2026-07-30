
```markdown
# UAP-Video-Detector

**UAP-Video-Detector** is an open-source computer vision pipeline designed to automate the filtering of mundane aerial objects from video streams. By training a robust baseline to highly accurately classify known objects—such as birds, planes, drones, and weather balloons—the system flags low-confidence detections or unclassifiable tracking vectors as potential **Unidentified Anomalous Phenomena (UAP)** for specialized review.

> **The Core Philosophy:** Filter out the knowns to isolate the unknowns.

---

## 📋 Spec Kit (Recommended)

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) so **specifications stay the source of truth** for what we build. Spec Kit is **open source and optional** — you can contribute without it — but it is **recommended** for feature work so requirements, plans, and tasks stay aligned before code changes.

### Prerequisites
* Python 3.11+
* [uv](https://docs.astral.sh/uv/) (Astral’s Python package manager)

### Platform & Shell Compatibility

**Operating Systems**: Windows, macOS, Linux  
**Shells**: Git Bash (recommended), PowerShell, Bash, Zsh, Command Prompt/CMD  
**Editors**: Cursor, VS Code, Claude Code, Zed, and 25+ other AI coding agents

### Install the Specify CLI

**Ephemeral (no permanent install):**
```bash
uvx --from git+https://github.com/github/spec-kit.git specify --help
```

**Persistent (recommended for regular contributors):**
```bash
uv tool install specify-cli
# Or pin a release: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
```

### Multi-Platform & Multi-Editor Support

This open source project supports multiple development environments and shells:

#### **For Cursor users** (current setup)
Already initialized! Skills are in `.cursor/skills/`. Use `/speckit-*` commands in chat.

#### **For VS Code + GitHub Copilot users**
```bash
cd UAP-Video-Detector
specify init --here --force --integration copilot --script bash  # Git Bash
# OR
specify init --here --force --integration copilot --script ps    # PowerShell
```

#### **For Claude Code users** 
```bash
cd UAP-Video-Detector
specify init --here --force --integration claude --script bash   # Git Bash  
# OR
specify init --here --force --integration claude --script ps     # PowerShell
```

#### **For other AI coding agents**

Spec Kit supports 30+ AI coding agents. Popular open source friendly options:

```bash
# Gemini CLI
specify init --here --force --integration gemini

# Codex CLI  
specify init --here --force --integration codex

# Cline (VS Code extension)
specify init --here --force --integration cline

# Zed editor
specify init --here --force --integration zed

# Tabnine CLI
specify init --here --force --integration tabnine

# See all 30+ available integrations
specify integration list

# Generic setup (bring your own agent)
specify init --here --force --integration generic --integration-options="--commands-dir .myagent/commands/"
```

### Shell Support

**Git Bash (recommended for cross-platform)**:
```bash
# All Spec Kit scripts work in Git Bash
cd UAP-Video-Detector
specify init --here --script sh
```

**PowerShell (Windows)**:
```powershell
# PowerShell-optimized scripts
cd UAP-Video-Detector  
specify init --here --script ps
```

**Command Prompt/CMD**:
```cmd
# Basic support via Python scripts
cd UAP-Video-Detector
specify init --here --script py
```

### Typical Spec-Driven Workflow

Regardless of your editor/agent, the workflow is the same:

1. **`/speckit-constitution`** — establish project principles  
2. **`/speckit-specify`** — define what and why (requirements)  
3. **`/speckit-plan`** — create technical implementation plan  
4. **`/speckit-tasks`** — generate actionable task breakdown  
5. **`/speckit-implement`** — execute the implementation  

**Optional quality gates**: `/speckit-clarify`, `/speckit-checklist`, `/speckit-analyze`, `/speckit-converge`

**Note**: Command syntax varies by agent:
- **Cursor/VS Code**: `/speckit-*` 
- **Claude Code**: `/speckit.*` or skills mode
- **Codex CLI**: `$speckit-*`
- **Generic**: Check your agent's documentation

Scaffolding lives in `.specify/` (templates, scripts, memory). Feature specs are written under `specs/` as you work. See the [Spec Kit Quick Start](https://github.github.io/spec-kit/quickstart.html) for details.

---

## 🚀 Quick Start

### Prerequisites
* Python 3.10 or higher
* Docker & Docker Compose (Optional, but recommended for instant environment setup)
* CUDA-compatible GPU (Highly recommended for real-time video processing)
```
<img width="320" height="320" alt="image" src="https://github.com/user-attachments/assets/e5fa3ef7-1510-4076-abac-e1e009351039" />
<br><br><br>

![alt text](uap-video-detector.png)


### Local Installation
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/UAP-Video-Detector.git](https://github.com/YOUR_USERNAME/UAP-Video-Detector.git)
   cd UAP-Video-Detector



2. **Set up a virtual environment:**
```bash
python -bin/venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


### Running the Detector

Place your input video file into the `data/raw/` folder and execute the main pipeline:

```bash
python src/main.py --source data/raw/sample_sky_feed.mp4 --conf 0.25

```

---

## 🏗️ Repository Structure

The architecture is built cleanly to separate ingestion, deep learning inference, and data orchestration workflows:

```text
uap-video-detector/
├── .cursor/skills/           # Spec Kit skills for Cursor (optional workflow)
├── .specify/                 # Spec Kit templates, scripts, and project memory
├── .github/
│   ├── ISSUE_TEMPLATE/       # Structured bug reports & feature requests
│   └── workflows/            # CI/CD pipelines (automated linting and testing)
├── config/                   # YAML files for tweaking YOLO confidence thresholds
├── data/
│   ├── raw/                  # Input videos and stream configurations
│   └── processed/            # Extracted crops and logs of anomalous events
├── models/                   # Custom trained weights (.pt files)
├── specs/                    # Feature specs/plans/tasks (created via Spec Kit)
├── src/                    
│   ├── ingestion/            # Video streaming and frame extraction logic
│   ├── inference/            # YOLO detection wrapper and anomaly filtering rules
│   ├── orchestration/        # Routing engines, local storage, or cloud logging handlers
│   ├── ui/                   
│   │   ├── app.py            # Streamlit dashboard layout or Frontend server entry
│   │   ├── components/       # Custom video players, metric displays, tables
│   │   └── assets/           # UI CSS, custom logos, or web styling
│   └── main.py               # Application entry point
├── tests/                    # Core pipeline unit tests (pytest)
├── docker-compose.yml        # Multi-container local execution environment
└── CONTRIBUTING.md           # Onboarding documentation for developers

```

---

## 🗺️ Project Roadmap

* [ ] **Phase 1:** Core pipeline architecture & basic tracking setup using pre-trained YOLO sets.
* [ ] **Phase 2:** Customized baseline fine-tuning specifically targeting edge-case aerial noise (refraction, birds, satellites).
* [ ] **Phase 3:** Automated extraction engine that clips and stores high-resolution snippets of unclassified visual bounding boxes.
* [ ] **Phase 4:** Agentic orchestration allowing logged anomalies to automatically generate metadata entries for community databases.
*** initiation Povoa01 suggestion 09JUL26***
* [ ] **Phase 1:** Initial input video analysis (file integrity, metadata extraction, multi extention formats).
* [ ] **Phase 2:** PreProcessing Stabilization-Frame enhancement-Noise Reduction (OpenCV or similar).
* [ ] **Phase 3:** YOLO (object detection - identification - localization).
* [ ] **Phase 4:** Tracking Process (frame association - identity - movement - trajectory).
* [ ] **Phase 5:** Scoring Process (UAP high score - crop - confidence level - known pattern - consistency - motion - size - shape).
* [ ] **Phase 6:** Forensic Analysis (motion - lighting - noise - compression - blur - scene integration).
* [ ] **Phase 7:** Analysis Report (final classification - forensic - scores - CGI/IA
*** finalization Povoa01 suggestion 09JUL26***
---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Git

### Installation
```bash
git clone https://github.com/YOUR_USERNAME/UAP-Video-Detector.git
cd UAP-Video-Detector
pip install -e .
```

### Run the Application

#### **Web Interface** (Recommended)
```bash
cd UAP-Video-Detector
streamlit run src/ui/app.py
```
Open `http://localhost:8501` in your browser.

#### **Command Line**
```bash
cd UAP-Video-Detector

# Analyze video with YOLO detection
python src/main.py path/to/your-video.mp4 --verbose

# Player-only mode (no detection)  
python src/main.py path/to/your-video.mp4 --backend null

# Save results to file
python src/main.py path/to/your-video.mp4 --output results.json
```

### Testing

```bash
cd UAP-Video-Detector

# 1. Core test suite (should show 168/168 passing)
pytest tests/ -q

# 2. Unit and contract tests specifically  
pytest tests/unit tests/contract -q

# 3. With coverage report
pytest tests/ --cov=src --cov-report=term-missing

# 4. Verbose output for detailed results
pytest tests/ -v
```

### Configuration

The system works out-of-the-box. Optional: Edit `config/detector.yaml`:

```yaml
backend: "null"           # null | yolo_world | yolov8 | yolov9 | custom
confidence_threshold: 0.25
device: "auto"            # auto | cpu | cuda
```

**Supported backends:**
- `null` - Player-only mode (no YOLO weights needed)
- `yolo_world` - Open-vocabulary detection  
- `yolov8/yolov9` - Standard YOLO models
- `custom` - Your trained weights

### YOLO Model Setup (Optional)

For aerial object detection, download YOLO weights to `models/` directory:

```bash
cd UAP-Video-Detector

# Create models directory
mkdir -p models

# Download YOLO-World weights (recommended)
# Visit: https://github.com/AILab-CVC/YOLO-World/releases
# Download yolov8s-world.pt to models/ folder

# Then update config/detector.yaml:
backend: "yolo_world"
weights_path: "models/yolov8s-world.pt"
```

**Target Classes:** airplane, helicopter, bird, drone

---

## 🤝 Contributing

We welcome contributions from software engineers, ML researchers, and data-driven UFOlogists alike! **All development environments are supported** — contribute using your preferred setup.

### Quick Contribution Setup

**Windows developers**:
```powershell
# Git + PowerShell + VS Code/Cursor
git clone https://github.com/YOUR_USERNAME/UAP-Video-Detector.git
cd UAP-Video-Detector
uv tool install specify-cli
specify init --here --integration copilot --script ps  # or cursor-agent
```

**macOS/Linux developers**:
```bash
# Git + Bash + any editor
git clone https://github.com/YOUR_USERNAME/UAP-Video-Detector.git
cd UAP-Video-Detector  
uv tool install specify-cli
specify init --here --integration claude --script sh   # or copilot/cursor-agent
```

### Contributing Process

1. Check out open tickets in our **Issues** tab
2. Review `CONTRIBUTING.md` for TDD requirements and code quality standards
3. Use **Spec Kit** for feature work (optional but recommended for alignment)
4. Open a Pull Request against the `main` branch

*For speculative ideas, hardware setup discussions, or philosophical questions, please use the **GitHub Discussions** tab rather than opening code issues.*

### Development Environment Support

This project supports **30+ AI coding agents** and **all major platforms**:
- **IDEs**: Cursor, VS Code, Zed, Android Studio, IntelliJ
- **CLI agents**: Claude Code, Gemini CLI, Codex CLI, Tabnine CLI
- **Shells**: Git Bash, PowerShell, Bash, Zsh, Command Prompt
- **OS**: Windows, macOS, Linux

--

## 🔍 Aerial Object Scanner Configuration

The scanner is **optional** and **replaceable** - the video player works independently.

### Supported Detection Backends

| Backend | Description | Weights Required |
|---------|-------------|------------------|
| `null` | No detection (player-only mode) | No |
| `yolo_world` | YOLO-World model for open-vocabulary detection | Yes |
| `yolov8` | YOLOv8 standard model | Yes |
| `yolov9` | YOLOv9 model | Yes |
| `custom` | Custom YOLO weights | Yes |

### Detector Configuration

Edit `config/detector.yaml` to swap detection backends:

```yaml
# Disable scanner (player-only mode)
backend: null

# Enable YOLO-World (recommended)
backend: "yolo_world"
weights_path: "models/yolov8s-world.pt"
confidence_threshold: 0.25
class_prompts:
  - airplane
  - helicopter  
  - bird
  - drone

# Use YOLOv8 standard
backend: "yolov8"
weights_path: "models/yolov8n.pt"

# Use YOLOv9
backend: "yolov9" 
weights_path: "models/yolov9c.pt"

# Use custom weights
backend: "custom"
weights_path: "models/my-custom-aerial.pt"
```

### Obtaining Model Weights

**YOLO-World (Recommended):**
```bash
# Download YOLO-World weights
mkdir -p models
curl -L "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s-world.pt" -o models/yolov8s-world.pt
```

**Standard YOLO:**
```bash
# YOLOv8 - will auto-download on first use
backend: "yolov8"
weights_path: "yolov8n.pt"  # Auto-downloads

# YOLOv9 - download manually
curl -L "https://github.com/WongKinYiu/yolov9/releases/download/v0.1/yolov9c.pt" -o models/yolov9c.pt
```

**Custom Training:**
```bash
# Train your own aerial detection model
yolo train data=aerial-dataset.yaml model=yolov8n.pt epochs=100
# Use the resulting best.pt as your custom weights
```

### Scanner Behavior

- **Missing/Invalid Configuration**: Falls back to null detector (player continues)
- **Missing Weights**: Shows warning, disables scanner (player continues)  
- **YOLO Import Error**: Uses null detector (player continues)
- **Runtime Errors**: Auto-disables scanner to prevent crashes

The video player **never crashes** due to scanner issues - it gracefully degrades to player-only mode.

---

## 🚀 Future Horizons & Roadmap

While our primary engine focuses on the physical elimination of known aerial objects, data integrity in the modern era requires us to look beyond the physical sky and into the pixels themselves.

As a secondary but increasingly critical long-term goal, the project aims to integrate pipeline layers designed to detect CGI, deepfakes, generative AI inserts, and advanced digital montages. Ensuring a video hasn't been synthetically manufactured is just as vital as ensuring it isn't a bird. While this is not our primary launch feature, building robust tools to flag digital manipulation is a high-priority milestone on our development roadmap.

---

## 📄 License

This project is licensed under the terms of the **GNU Affero General Public License v3.0 (AGPL-3.0)**. This guarantees that modifications to the detection engines remain open and accessible to the scientific community.
