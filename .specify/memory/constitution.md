<!--
Sync Impact Report:
- Version change: [INITIAL] → 1.0.0
- New constitution with 7 core principles covering open source development, SOLID principles, Python best practices, and real-time AI video processing
- Added sections: Technical Standards and Development Workflow
- Templates requiring updates: ✅ Updated plan-template.md constitution check / ✅ Updated spec-template.md alignment / ✅ Updated tasks-template.md principle-driven categorization
- Follow-up TODOs: None - all placeholders filled with concrete values
-->

# UAP-Video-Detector Constitution

## Core Principles

### I. Open Source Transparency (NON-NEGOTIABLE)
All code, models, datasets, and documentation MUST remain publicly accessible under AGPL-3.0 license. No proprietary dependencies or closed-source components allowed. Community contributions drive scientific advancement. Every feature enhancement, bug fix, and model improvement MUST be shared with the research community to elevate UAP detection standards globally.

**Rationale**: Scientific integrity demands reproducible, auditable systems. UAP research requires open collaboration to eliminate bias and ensure credible analysis.

### II. SOLID Architecture Principles
Code MUST follow SOLID design principles: Single Responsibility (each class/function has one purpose), Open/Closed (extensible without modification), Liskov Substitution (interchangeable components), Interface Segregation (focused contracts), and Dependency Inversion (abstractions over concretions). Every module MUST be independently testable and replaceable.

**Rationale**: Computer vision pipelines grow complex rapidly. SOLID principles ensure maintainable, scalable architecture as detection algorithms evolve.

### III. Loose Coupling & Component Isolation
System components (ingestion, inference, orchestration, UI) MUST operate independently with well-defined interfaces. No direct dependencies between layers. Use dependency injection, event-driven patterns, and clear API contracts. Each component MUST be deployable, testable, and replaceable in isolation.

**Rationale**: Real-time video processing requires modular architecture for performance scaling, algorithm swapping, and independent optimization of pipeline stages.

### IV. Parameterized Configuration (NON-NEGOTIABLE)
All behavior MUST be externally configurable via YAML files, environment variables, or CLI parameters. No hardcoded thresholds, file paths, model weights, or processing parameters in source code. Configuration changes MUST NOT require code recompilation or deployment.

**Rationale**: UAP detection requires constant threshold tuning, model switching, and parameter optimization. Research workflows demand rapid experimentation without code changes.

### V. Component-Based Development
Every feature MUST start as a standalone, reusable component with clear interfaces. Components MUST be self-contained, independently documented, and expose CLI interfaces. Libraries before applications, modules before monoliths. Shared functionality extracted into separate packages.

**Rationale**: Computer vision research benefits from composable, interchangeable components. Different detection algorithms, preprocessing techniques, and output formats should plug together seamlessly.

### VI. DRY Principle Enforcement
Eliminate all code duplication. Extract common functionality into shared utilities, base classes, or configuration-driven templates. Data processing logic, validation rules, and algorithm implementations MUST NOT be duplicated across modules. Use inheritance, composition, and configuration to remove redundancy.

**Rationale**: Video processing pipelines contain repetitive patterns (frame extraction, bounding box manipulation, confidence filtering). Code duplication creates maintenance burden and introduces inconsistent behavior.

### VII. Python Performance & Real-Time Processing
Python code MUST be optimized for real-time video processing: vectorized operations with NumPy, efficient OpenCV usage, proper memory management, and asynchronous I/O where applicable. CPU-bound operations MUST support GPU acceleration. Memory leaks and blocking operations are unacceptable in production pipelines.

**Rationale**: Real-time UAP detection requires sub-second frame processing. Python's flexibility must not compromise performance in time-critical computer vision workflows.

## Technical Standards

### Testing Requirements
Test-Driven Development (TDD) MUST be followed for all computer vision components. Write failing tests first, implement minimal code to pass, then refactor. Mock hardware dependencies (cameras, GPU inference) in unit tests. Achieve 85%+ code coverage. Integration tests MUST validate end-to-end video processing workflows.

### Code Quality Gates
All code MUST pass Black formatting, Ruff linting, and type checking before merge. Use pytest for all testing. Follow PEP 8 conventions. Document all public APIs with docstrings. No warnings or linting errors allowed in main branch.

### YOLO Integration Standards
YOLO model integration MUST support multiple versions (YOLOv8, YOLOv9, custom weights). Inference calls MUST be abstracted behind interfaces to enable algorithm swapping. Model loading MUST be lazy and configurable. Support both CPU and GPU acceleration paths.

## Development Workflow

### Version Control
Feature branches for all changes. Pull requests require code review and passing CI/CD. Commit messages MUST follow conventional commits format. No direct pushes to main branch. Tag releases with semantic versioning.

### AI Model Management
Model weights (.pt files) versioned separately from code. Configuration files specify model versions and sources. Support local and remote model loading. Document model performance benchmarks and accuracy metrics.

### Performance Monitoring
Real-time processing performance MUST be monitored and logged. Frame processing latency, memory usage, and GPU utilization tracked. Performance regressions in CI pipeline trigger alerts.

## Governance

This constitution supersedes all other development practices. Amendments require documented justification, community discussion, and migration plan. All pull requests MUST verify constitutional compliance. Architecture decisions MUST align with stated principles.

Complexity that violates these principles requires explicit justification in design documents. Use `CONTRIBUTING.md` for runtime development guidance and project-specific workflows.

**Version**: 1.0.0 | **Ratified**: 2026-07-29 | **Last Amended**: 2026-07-29