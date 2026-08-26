# Migration Cleanup Checklist: Spec-Kit → Skill-Driven Development

**Start Date**: 2026-08-26  
**Target Completion**: TBD  
**Status**: In Progress

This checklist tracks the removal of legacy Spec-Kit artifacts and confirms the transition to consolidated Skill-Driven Development (SDD).

---

## Phase 1: Verification & Backup

> **Important**: Review and backup legacy artifacts before deletion. This phase is READ-ONLY for safety.

### Audit Legacy Artifacts

- [ ] **Verify `.specify/` contents**:
  - [ ] List all templates in `/.specify/templates/`
  - [ ] List all scripts in `/.specify/scripts/` (bash/, powershell/)
  - [ ] Review `/.specify/integration.json` and `/.specify/integrations/`
  - [ ] Confirm no custom logic in `/.specify/memory/` needed for SDD

- [ ] **Verify `.github/agents/` contents**:
  - [ ] Confirm all 10 `speckit.*.agent.md` files listed below exist:
    - [ ] `speckit.analyze.agent.md`
    - [ ] `speckit.checklist.agent.md`
    - [ ] `speckit.clarify.agent.md`
    - [ ] `speckit.constitution.agent.md`
    - [ ] `speckit.converge.agent.md`
    - [ ] `speckit.implement.agent.md`
    - [ ] `speckit.plan.agent.md`
    - [ ] `speckit.specify.agent.md`
    - [ ] `speckit.tasks.agent.md`
    - [ ] `speckit.taskstoissues.agent.md`

- [ ] **Verify `.github/prompts/` contents**:
  - [ ] Confirm all 10 `speckit.*.prompt.md` files listed below exist (mirrors agents)

- [ ] **Verify `.claude/skills/speckit-*/` contents**:
  - [ ] `/.claude/skills/speckit-analyze/SKILL.md`
  - [ ] `/.claude/skills/speckit-checklist/SKILL.md`
  - [ ] `/.claude/skills/speckit-clarify/SKILL.md`
  - [ ] `/.claude/skills/speckit-constitution/SKILL.md`
  - [ ] `/.claude/skills/speckit-converge/SKILL.md`
  - [ ] `/.claude/skills/speckit-implement/SKILL.md`
  - [ ] `/.claude/skills/speckit-plan/SKILL.md`
  - [ ] `/.claude/skills/speckit-specify/SKILL.md`
  - [ ] `/.claude/skills/speckit-tasks/SKILL.md`
  - [ ] `/.claude/skills/speckit-taskstoissues/SKILL.md`

- [ ] **Verify `.cursor/` structure** (if Cursor integration exists):
  - [ ] Check for `.cursor/agents/` and `.cursor/prompts/` (mirror of `.github/`)
  - [ ] Check for `.cursor/skills/speckit-*/` directory

- [ ] **Backup command** (optional, for safety):
  ```bash
  # Create archive of legacy artifacts before deletion
  git checkout -b backup/speckit-legacy-$(date +%Y%m%d-%H%M%S)
  # Or manually copy to external storage
  ```

### Verify New Consolidated Skill

- [ ] **Confirm new SKILL.md created**:
  - [ ] `/.claude/skills/yolo-video-player/SKILL.md` exists and is readable
  - [ ] File contains all sections: Overview, Technical Context, User Stories, Checklist, Constitution
  - [ ] Checklist is actionable and references correct source files
  - [ ] No broken links or missing sections

---

## Phase 2: Safe Deletion of Legacy Artifacts

> **Important**: Delete in dependency order to avoid breaking active development. Test locally first.

### Step 1: Disable Spec-Kit Commands (No Functionality Loss)

- [ ] Rename `.github/agents/` to `.github/agents.bak/` (temp; reverses easily)
  ```bash
  mv .github/agents .github/agents.bak
  ```

- [ ] Rename `.github/prompts/` to `.github/prompts.bak/` (temp; reverses easily)
  ```bash
  mv .github/prompts .github/prompts.bak
  ```

- [ ] Rename `/.claude/skills/speckit-*` directories (temp; reverses easily)
  ```bash
  mv .claude/skills/speckit-analyze .claude/skills/.speckit-analyze.bak
  # (repeat for all 10 speckit-* directories)
  ```

- [ ] **Test**: Verify that Cursor/VS Code no longer offer `/speckit-*` commands
  - [ ] Reload editor or clear skill cache if needed
  - [ ] Confirm `/yolo-video-player` skill is available and loads correctly

- [ ] Commit this step locally: `git commit -m "Temporarily disable legacy Spec-Kit skills"`

### Step 2: Delete Legacy Feature Specs (After Content Consolidated)

> **Prerequisite**: Verify new SKILL.md has all content from `specs/001-yolo-video-player/`

- [ ] Remove entire directory: `specs/001-yolo-video-player/`
  ```bash
  rm -r specs/001-yolo-video-player/
  ```

- [ ] **Verify**: 
  - [ ] `ls specs/` should be empty or only show non-legacy features
  - [ ] No broken links in README or active docs

- [ ] Commit: `git commit -m "Remove legacy spec files (content consolidated in .claude/skills/yolo-video-player/SKILL.md)"`

### Step 3: Delete Legacy Specify Infrastructure

> **Note**: If other projects/features use Spec-Kit, preserve `.specify/` structure but remove project-specific integrations.

- [ ] **Option A** (if this is the only Spec-Kit project): Remove entire directory
  ```bash
  rm -r .specify/
  ```

- [ ] **Option B** (if other projects use Spec-Kit): Archive project-specific files only
  ```bash
  # Keep .specify/ structure, remove project-specific templates/scripts
  rm -r .specify/templates/
  rm -r .specify/scripts/
  rm .specify/feature.json
  rm .specify/init-options.json
  # Keep .specify/integrations/ and .specify/memory/ if used by other projects
  ```

- [ ] Commit: `git commit -m "Remove Spec-Kit infrastructure (.specify/); migrated to Skill-Driven approach"`

### Step 4: Finalize: Permanently Delete Backed-Up Artifacts

> **Only after confirmation that dev workflow is unaffected and CI/CD passes**

- [ ] Delete `.github/agents.bak/` directory
  ```bash
  rm -r .github/agents.bak
  ```

- [ ] Delete `.github/prompts.bak/` directory
  ```bash
  rm -r .github/prompts.bak
  ```

- [ ] Delete all `.claude/skills/.speckit-*.bak/` directories
  ```bash
  rm -r .claude/skills/.speckit-*.bak
  ```

- [ ] Delete `.cursor/agents.bak/`, `.cursor/prompts.bak/`, `.cursor/skills/.speckit-*.bak/` (if Cursor integration)
  ```bash
  rm -r .cursor/agents.bak
  rm -r .cursor/prompts.bak
  rm -r .cursor/skills/.speckit-*.bak
  ```

- [ ] Commit: `git commit -m "Finalize Spec-Kit removal; transition complete"`

---

## Phase 3: Update Documentation & Configuration

### Update README.md

- [ ] **Replace Spec Kit section** with **Skill-Driven Development section**:
  - [ ] Remove "📋 Spec Kit (Recommended)" section and all `specify` installation/usage instructions
  - [ ] Add new "📋 Skill-Driven Development" section explaining the consolidated approach
  - [ ] Document available skills (e.g., `/yolo-video-player`)
  - [ ] Add contributor quickstart (3-step guide to pick a skill, trigger agent, submit changes)
  - [ ] Emphasize low token overhead and open-source contributor friendliness

- [ ] **Example sections to replace**:
  ```markdown
  OLD: ### Prerequisites
  * Python 3.11+
  * [uv](https://docs.astral.sh/uv/) (Astral's Python package manager)

  OLD: ### Install the Specify CLI
  ...all uv/specify commands...

  OLD: ### Typical Spec-Driven Workflow
  1. /speckit-constitution
  2. /speckit-specify
  3. /speckit-plan
  4. /speckit-tasks
  5. /speckit-implement

  NEW: ### Skill-Driven Development (SDD)
  This project uses lightweight, consolidated **Skill Files** (`SKILL.md`) to keep AI context fast, lean, and open-source friendly.

  **Available Skills:**
  - [yolo-video-player](`.claude/skills/yolo-video-player/SKILL.md`) — Video uploader, player, and YOLO detection

  **How to Contribute:**
  1. Pick a skill file in `.claude/skills/*/SKILL.md`
  2. Run the skill in Cursor/Claude Code: `/yolo-video-player` or `skills: yolo-video-player`
  3. Follow the consolidated checklist to implement your feature
  4. Submit a pull request

  No complex multi-file setup, no heavy token overhead — just one focused skill file per feature.
  ```

- [ ] **Review full README** for any other references to Spec-Kit or specify CLI

### Update Project Config Files

- [ ] **`.github/workflows/` (if CI/CD exists)**:
  - [ ] Remove any jobs that run `specify` commands (e.g., `specify init`, `specify validate`)
  - [ ] Update CI/CD to reference new SKILL.md instead of legacy spec files (if applicable)

- [ ] **`pyproject.toml` (if applicable)**:
  - [ ] Remove any Spec-Kit-related scripts or test commands
  - [ ] Ensure test discovery still points to `tests/` directory

- [ ] **`.gitignore` (if applicable)**:
  - [ ] Remove patterns that ignore `.specify/` outputs (if `.specify/` is now deleted)
  - [ ] Confirm `specs/001-yolo-video-player/` is git-tracked or ignored consistently

### Update Contribution Guidelines

- [ ] **Update `CONTRIBUTING.md`**:
  - [ ] Replace Spec-Kit workflow with Skill-Driven workflow
  - [ ] Link to new SKILL.md files as the source of truth
  - [ ] Explain loose coupling principles and architecture constraints
  - [ ] Remove references to `/speckit-*` commands; replace with skill activation (e.g., `/yolo-video-player`)

---

## Phase 4: Testing & Validation

### Local Testing

- [ ] **Verify Cursor/VS Code + Claude Code agents still work**:
  - [ ] Open editor on the repository
  - [ ] Confirm `/yolo-video-player` skill loads and is invocable
  - [ ] Confirm no `/speckit-*` commands appear in autocomplete (if successfully disabled)

- [ ] **Verify file structure integrity**:
  ```bash
  find . -type f -name "*.md" | grep -E "(spec|plan|task)" | wc -l
  # Should show only non-legacy spec files or zero
  ```

- [ ] **Verify README renders correctly** (if GitHub):
  - [ ] Visit repository on GitHub
  - [ ] Confirm README displays without broken links
  - [ ] Confirm skill links (e.g., to `.claude/skills/yolo-video-player/SKILL.md`) are valid

### CI/CD Testing

- [ ] **Run existing test suite** (if applicable):
  ```bash
  pytest tests/ -q --cov=src --cov-fail-under=85
  ```

- [ ] **Confirm no broken imports or references**:
  ```bash
  grep -r "speckit" . --include="*.py" --include="*.md" --include="*.yaml" | wc -l
  # Should return 0 (no lingering speckit references in code)
  ```

- [ ] **If GitHub Actions CI exists**: Trigger workflow and confirm green
  - [ ] Check for any workflow steps that reference `.specify/` or `speckit`
  - [ ] Update workflow to skip those steps or remove them

### Manual Acceptance

- [ ] **Contributor onboarding test**: Ask a team member to:
  - [ ] Clone repository
  - [ ] Open in Cursor or VS Code + Copilot
  - [ ] Activate `/yolo-video-player` skill
  - [ ] Read SKILL.md checklist
  - [ ] Confirm clarity and actionability (no references to deleted files)
  - [ ] Record feedback

---

## Phase 5: Rollback Plan (If Needed)

> **Only use if issues arise after deletion**

### Restore from Git History

```bash
# If changes not yet pushed to remote, use git history
git reflog | grep "Spec-Kit removal" # Find commit SHA
git revert <sha> # Revert deletion commit

# If changes already pushed, revert on remote
git push origin revert/<sha>
```

### Restore from Backup Branch

```bash
# If backup branch was created in Phase 1
git merge backup/speckit-legacy-<date>
git push origin main
```

### Manual Restore (Last Resort)

```bash
# If backup directory exists locally
mv .github/agents.bak .github/agents
mv .github/prompts.bak .github/prompts
mv .claude/skills/.speckit-*.bak .claude/skills/speckit-*
# Etc.
```

---

## Sign-Off

- [ ] **Migration Lead**: ________________________  Date: _______
- [ ] **Code Review**: ________________________  Date: _______
- [ ] **QA/Testing**: ________________________  Date: _______

**Notes:**
```
[Space for migration notes, issues encountered, and lessons learned]
```

---

## Appendix: File Inventory

### Directories to Delete

```
.specify/
.github/agents/
.github/prompts/
.claude/skills/speckit-analyze/
.claude/skills/speckit-checklist/
.claude/skills/speckit-clarify/
.claude/skills/speckit-constitution/
.claude/skills/speckit-converge/
.claude/skills/speckit-implement/
.claude/skills/speckit-plan/
.claude/skills/speckit-specify/
.claude/skills/speckit-tasks/
.claude/skills/speckit-taskstoissues/
specs/001-yolo-video-player/
```

### Directory to Create/Verify

```
.claude/skills/yolo-video-player/
```

### Files to Update

```
README.md
CONTRIBUTING.md
.github/workflows/*.yml (if applicable)
pyproject.toml (if applicable)
.gitignore (if applicable)
```

### Files Consolidated Into

```
.claude/skills/yolo-video-player/SKILL.md
  ↑ Replaces:
    - specs/001-yolo-video-player/spec.md
    - specs/001-yolo-video-player/plan.md
    - specs/001-yolo-video-player/tasks.md
    - specs/001-yolo-video-player/data-model.md
    - specs/001-yolo-video-player/contracts/*.md
    - .claude/skills/speckit-*/*.md (all 10)
    - .github/agents/speckit.*.agent.md (all 10)
    - .github/prompts/speckit.*.prompt.md (all 10)
```
