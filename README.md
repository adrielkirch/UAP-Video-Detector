
```markdown
# UAP-Video-Detector

**UAP-Video-Detector** is an open-source computer vision pipeline designed to automate the filtering of mundane aerial objects from video streams. By training a robust baseline to highly accurately classify known objects—such as birds, planes, drones, and weather balloons—the system flags low-confidence detections or unclassifiable tracking vectors as potential **Unidentified Anomalous Phenomena (UAP)** for specialized review.

> **The Core Philosophy:** Filter out the knowns to isolate the unknowns.

---

## 📋 Skill-Driven Development

This project uses **lightweight, consolidated Skill Files** (`.claude/skills/*/SKILL.md`) to keep AI context fast, lean, and open-source contributor-friendly. Each skill consolidates requirements, implementation plans, and actionable tasks in a single file — no multi-file specs, no external scaffolding, no heavy token overhead.

### Supported Editors & AI Agents

**Editors**: Cursor, VS Code (GitHub Copilot / Claude Code), Zed, Cline, and other AI coding agents  
**Operating Systems**: Windows, macOS, Linux  
**Shells**: Git Bash (recommended), PowerShell, Bash, Zsh, CMD

### Available Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| **yolo-video-player** | [`.claude/skills/yolo-video-player/SKILL.md`](.claude/skills/yolo-video-player/SKILL.md) | Video uploader, HTML5 player, and live YOLO detection for aerial objects (airplane, helicopter, bird, drone) |

More skills coming as features are developed.

### How to Contribute

#### Step 1: Pick a Skill

Open the skill file (e.g., [`.claude/skills/yolo-video-player/SKILL.md`](.claude/skills/yolo-video-player/SKILL.md)) and review the **Overview** and **Execution Checklist** sections.

#### Step 2: Activate the Skill in Your Editor

**In Cursor (recommended):**
```
Type: /yolo-video-player
or: skills: yolo-video-player
```

**In VS Code + GitHub Copilot / Claude Code:**
```
Type: /yolo-video-player
or: skills: yolo-video-player
(or use the Copilot chat command system for your agent)
```

**In Other Editors:**
Refer to your editor's documentation for activating custom skills. The skill file path is `.claude/skills/yolo-video-player/SKILL.md`.

#### Step 3: Follow the Checklist

The skill file contains a step-by-step **Execution Checklist** organized by phases. Implement each phase in order; TDD is required (write failing tests first, confirm they fail, implement, confirm green).

#### Step 4: Submit Your PR

Commit your changes and open a pull request. Reference the skill file and the phases you've completed.

### Why Skill-Driven Development?

- **Low Token Overhead**: One consolidated file per feature, not 20+ fragmented templates
- **Open-Source Friendly**: Contributors don't need complex tooling or large token budgets
- **Fast Context Load**: AI agents load only the specific skill they need
- **No External Dependencies**: No CLI tools, no external scaffolding scripts, no multi-file sync
- **Deterministic Workflows**: Clear, inline checklists and directives replace multi-step agent commands
- **Easier Maintenance**: Single source of truth per feature; no spec drift between files

### Project Structure

```
.claude/skills/                           # Consolidated skill files
└── yolo-video-player/
    └── SKILL.md                          # Single unified skill (replaces multi-file specs)

src/
├── ingestion/                            # Video upload & playback
├── inference/                            # Detection & YOLO interface
├── orchestration/                        # Binding player ↔ detector
└── ui/                                   # Streamlit UI layer

config/
├── video_player.yaml                    # Player config (formats, sessions)
└── detector.yaml                        # Detector config (weights, thresholds, device)

tests/
├── unit/                                 # Isolated module tests
├── contract/                             # Interface contract tests
└── integration/                          # End-to-end scenarios
```

### Migration Notes

**This project recently migrated from GitHub Spec-Kit to Skill-Driven Development** to reduce complexity and lower the barrier for open-source contributors. Legacy Spec-Kit artifacts (`.specify/`, `/.github/agents/`, `/.github/prompts/`, `/.claude/skills/speckit-*/`) have been consolidated into `.claude/skills/yolo-video-player/SKILL.md`.

For details on this migration, see [MIGRATION_CLEANUP.md](MIGRATION_CLEANUP.md).

---

## 🚀 Quick Start

### Prerequisites
* Python 3.10 or higher
* Docker & Docker Compose (Optional, but recommended for instant environment setup)
* CUDA-compatible GPU (Highly recommended for real-time video processing)

<img width="320" height="320" alt="image" src="https://github.com/user-attachments/assets/e5fa3ef7-1510-4076-abac-e1e009351039" />
<br><br><br>

![alt text](uap-video-detector.png)


### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/UAP-Video-Detector.git
   cd UAP-Video-Detector
   ```

2. **Create a virtual environment** (do this once after cloning).

   A virtual environment is a project-local folder (`.venv`) with its own Python interpreter and packages. It keeps Streamlit, OpenCV, and YOLO isolated from your system Python.

   ```bash
   python -m venv .venv
   ```

   On macOS or Linux, use `python3 -m venv .venv` if the `python` command is not found.

3. **Activate the virtual environment** (do this every time you open a new terminal in this project).

   | Shell | Activate command |
   |-------|------------------|
   | Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
   | Windows Command Prompt | `.venv\Scripts\activate.bat` |
   | macOS / Linux (bash, zsh) | `source .venv/bin/activate` |

   Activation worked if your prompt starts with `(.venv)`.

   If PowerShell blocks the script with an execution-policy error, run this once in the same window and activate again:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

   Leave the environment later with `deactivate`.

4. **Install dependencies** (the virtual environment must be active):
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Running the Detector

**Web interface (recommended):**

```bash
streamlit run src/ui/app.py
```

Then open `http://localhost:8501` in your browser.

The video layer is an HTML5 / Plyr player (not `st.video`). Upload sits in the **center** until a file is loaded. `.streamlit/config.toml` turns on `enableStaticServing` so playable copies can be served from `src/ui/static/play/`. Restart Streamlit after changing that file. Annotated scan output is remuxed to H.264 with `imageio-ffmpeg` (already in `requirements.txt`).

**Command line:**

```bash
python src/main.py path/to/your-video.mp4 --verbose
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
│   │   ├── app.py            # Streamlit dashboard (centered upload + player)
│   │   ├── components/       # HTML5/Plyr player, uploader, overlays
│   │   └── static/           # Served player assets (Plyr + staged play copies)
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

Create and activate a virtual environment first (see **Local Installation** above), then install the project:

```bash
git clone https://github.com/YOUR_USERNAME/UAP-Video-Detector.git
cd UAP-Video-Detector
python -m venv .venv
# Windows PowerShell:  .\.venv\Scripts\Activate.ps1
# Windows CMD:         .venv\Scripts\activate.bat
# macOS / Linux:       source .venv/bin/activate
python -m pip install --upgrade pip
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
