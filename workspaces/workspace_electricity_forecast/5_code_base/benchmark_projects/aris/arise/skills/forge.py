from __future__ import annotations

import sys

from arise.llm import llm_call_structured, llm_call


def _log(msg: str):
    print(f"[ARISE:forge] {msg}", flush=True)
import ast
import re

from arise.prompts import (
    ADVERSARIAL_TEST_PROMPT,
    GAP_DETECTION_PROMPT,
    PATCH_PROMPT,
    SYNTHESIS_PROMPT,
    TEST_GENERATION_PROMPT,
    REFINEMENT_PROMPT,
)
from arise.skills.sandbox import Sandbox
from arise.types import GapAnalysis, Skill, SkillOrigin, SkillStatus, Trajectory


def _extract_imports(code: str) -> set[str]:
    """Extract top-level module names from all import statements in code."""
    modules: set[str] = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        # Fallback: regex-based extraction
        for match in re.finditer(r'^\s*(?:import|from)\s+(\w+)', code, re.MULTILINE):
            modules.add(match.group(1))
        return modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split('.')[0])
    return modules


_DYNAMIC_IMPORT_PATTERNS = [
    re.compile(r'__import__\s*\(\s*["\'](\w+)'),           # __import__("os")
    re.compile(r'importlib\.import_module\s*\(\s*["\'](\w+)'),  # importlib.import_module("os")
    re.compile(r'exec\s*\(\s*["\'].*?\bimport\b'),         # exec("import os")
    re.compile(r'eval\s*\(\s*["\'].*?import'),              # eval("__import__('os')")
]


def _detect_dynamic_imports(code: str) -> tuple[set[str], bool]:
    """Detect dynamic import patterns. Returns (module_names, has_unsafe_exec)."""
    modules: set[str] = set()
    has_unsafe = False
    for i, pattern in enumerate(_DYNAMIC_IMPORT_PATTERNS):
        for match in pattern.finditer(code):
            if i < 2:
                # __import__ and importlib — we can extract the module name
                modules.add(match.group(1))
            else:
                # exec/eval with import — can't reliably extract, flag as unsafe
                has_unsafe = True
    return modules, has_unsafe


def _check_imports(code: str, allowed: list[str]) -> list[str]:
    """Return list of disallowed imports found in code. Empty list = all good.

    Checks both static imports (import/from) and dynamic imports
    (__import__, importlib.import_module, exec/eval with import).
    """
    static = _extract_imports(code)
    dynamic, has_unsafe = _detect_dynamic_imports(code)

    allowed_set = set(allowed)
    disallowed = sorted((static | dynamic) - allowed_set)

    if has_unsafe:
        disallowed.append("__dynamic_import__")

    return disallowed


class SkillForge:
    def __init__(self, model: str, sandbox: Sandbox, max_retries: int = 3, allowed_imports: list[str] | None = None, registry=None, llm_router=None):
        self.model = model
        self.sandbox = sandbox
        self.max_retries = max_retries
        self.allowed_imports = allowed_imports
        self.registry = registry  # SkillRegistry | None
        self.llm_router = llm_router  # LLMRouter | None

    def detect_gaps(
        self,
        failed_trajectories: list[Trajectory],
        library,  # SkillLibrary — avoid circular import
    ) -> list[GapAnalysis]:
        active = library.get_active_skills()
        tools_desc = "\n".join(
            f"- {s.name}: {s.description}" for s in active
        ) or "(none)"

        traj_desc = "\n\n".join(
            f"Task: {t.task}\nOutcome: {t.outcome}\nReward: {t.reward}\nSteps:\n"
            + "\n".join(
                f"  - Action: {s.action}, Error: {s.error}" for s in t.steps
            )
            for t in failed_trajectories[:10]
        )

        prompt = GAP_DETECTION_PROMPT.format(
            trajectories=traj_desc,
            existing_tools=tools_desc,
        )

        _log("Detecting capability gaps...")
        model = self.llm_router.get_model("gap_detection") if self.llm_router else self.model
        raw = llm_call_structured(
            [{"role": "user", "content": prompt}],
            model=model,
        )

        if isinstance(raw, list):
            return [GapAnalysis(**g) for g in raw]
        return []

    def synthesize(
        self,
        gap: GapAnalysis,
        library,
        example_trajectories: list[Trajectory] | None = None,
    ) -> Skill:
        # Check registry for a pre-built skill before synthesizing
        if self.registry is not None:
            try:
                entries = self.registry.search(gap.description, limit=3)
                if entries:
                    best = entries[0]
                    if best.avg_success_rate > 0.7:
                        try:
                            skill = self.registry.pull(best.name)
                            result = self.sandbox.test_skill(skill)
                            if result.success:
                                _log(f"Found '{best.name}' in registry, skipping synthesis")
                                return skill
                        except Exception:
                            pass
            except Exception:
                pass

        active = library.get_active_skills()
        tools_desc = "\n".join(
            f"- {s.name}: {s.description}" for s in active
        ) or "(none)"

        evidence = "\n".join(gap.evidence) if gap.evidence else "(none)"

        import_constraint = ""
        if self.allowed_imports:
            import_constraint = (
                f"\n\nALLOWED IMPORTS (you may ONLY use these modules): "
                f"{', '.join(self.allowed_imports)}\n"
                f"Do NOT import any module not in this list."
            )

        prompt = SYNTHESIS_PROMPT.format(
            description=gap.description,
            signature=gap.suggested_signature,
            existing_tools=tools_desc,
            evidence=evidence,
        ) + import_constraint

        _log(f"Synthesizing '{gap.suggested_name}'...")
        model = self.llm_router.get_model("synthesis") if self.llm_router else self.model
        raw = llm_call_structured(
            [{"role": "user", "content": prompt}],
            model=model,
        )

        skill = Skill(
            name=raw["name"],
            description=raw.get("description", gap.description),
            implementation=raw["implementation"],
            test_suite=raw.get("test_suite", ""),
            origin=SkillOrigin.SYNTHESIZED,
        )

        # Validate in sandbox, refine if needed
        for attempt in range(self.max_retries):
            # Check import restrictions before sandbox testing
            if self.allowed_imports:
                disallowed = _check_imports(skill.implementation, self.allowed_imports)
                if disallowed:
                    _log(f"Disallowed imports found: {disallowed}, refining...")
                    skill = self.refine(
                        skill,
                        f"Disallowed imports: {', '.join(disallowed)}. "
                        f"Only these imports are allowed: {', '.join(self.allowed_imports)}",
                        context=evidence,
                    )
                    continue

            _log(f"Testing in sandbox (attempt {attempt + 1}/{self.max_retries})...")
            result = self.sandbox.test_skill(skill)
            if self.llm_router:
                self.llm_router.record("synthesis", model, result.success)
            if result.success:
                _log(f"All {result.total_passed} tests passed!")
                return skill

            errors = "\n".join(
                f"{t.test_name}: {t.error}" for t in result.test_results if not t.passed
            )
            if result.stderr:
                errors += f"\nStderr: {result.stderr}"

            _log(f"Tests failed ({result.total_failed} failures), refining...")
            skill = self.refine(skill, errors, context=evidence)

        return skill

    def refine(self, skill: Skill, feedback: str, context: str = "(none)") -> Skill:
        _log(f"Refining '{skill.name}'...")
        prompt = REFINEMENT_PROMPT.format(
            name=skill.name,
            description=skill.description,
            context=context,
            implementation=skill.implementation,
            test_suite=skill.test_suite,
            feedback=feedback,
        )

        model = self.llm_router.get_model("refinement") if self.llm_router else self.model
        raw = llm_call_structured(
            [{"role": "user", "content": prompt}],
            model=model,
        )

        return Skill(
            name=skill.name,
            description=skill.description,
            implementation=raw["implementation"],
            test_suite=raw.get("test_suite", skill.test_suite),
            version=skill.version + 1,
            origin=SkillOrigin.REFINED,
            parent_id=skill.id,
        )

    def patch(self, skill: Skill, failures: list[Trajectory]) -> Skill:
        """Apply a minimal fix to an existing skill based on specific failures."""
        failure_desc = "\n\n".join(
            f"Task: {t.task}\nError: {t.steps[-1].error if t.steps and t.steps[-1].error else t.outcome}"
            for t in failures[:5]
        )

        model = self.llm_router.get_model("refinement") if self.llm_router else self.model

        raw = llm_call_structured(
            [{"role": "user", "content": PATCH_PROMPT.format(
                name=skill.name,
                description=skill.description,
                implementation=skill.implementation,
                failures=failure_desc,
            )}],
            model=model,
        )

        return Skill(
            name=skill.name,
            description=skill.description,
            implementation=raw["implementation"],
            test_suite=skill.test_suite,
            version=skill.version + 1,
            origin=SkillOrigin.PATCHED,
            parent_id=skill.id,
        )

    def compose(self, skill_a: Skill, skill_b: Skill, description: str) -> Skill:
        """Compose two skills into a higher-level skill.

        Note: This method is available for manual use but is NOT called automatically
        during the evolution cycle. Automatic composition is planned for a future release.
        """
        prompt = f"""\
Combine these two Python tools into a single higher-level tool.

TOOL A — {skill_a.name}:
```python
{skill_a.implementation}
```

TOOL B — {skill_b.name}:
```python
{skill_b.implementation}
```

DESIRED BEHAVIOR:
{description}

Create a new function that uses both tools. Include the implementations of both tools in the output.

Return ONLY a JSON object:
{{
    "name": "composed_function_name",
    "description": "One-line description",
    "implementation": "full Python source code including both original functions and the new composed function",
    "test_suite": "test code with test_* functions"
}}
"""

        raw = llm_call_structured(
            [{"role": "user", "content": prompt}],
            model=self.model,
        )

        skill = Skill(
            name=raw["name"],
            description=raw.get("description", description),
            implementation=raw["implementation"],
            test_suite=raw.get("test_suite", ""),
            origin=SkillOrigin.COMPOSED,
        )

        # Validate
        result = self.sandbox.test_skill(skill)
        if not result.success:
            errors = "\n".join(
                f"{t.test_name}: {t.error}" for t in result.test_results if not t.passed
            )
            skill = self.refine(skill, errors)

        return skill

    def adversarial_validate(self, skill: Skill) -> tuple[bool, str]:
        """Run adversarial tests against a skill. Returns (passed, feedback)."""
        _log(f"Adversarial testing '{skill.name}'...")
        prompt = ADVERSARIAL_TEST_PROMPT.format(
            name=skill.name,
            description=skill.description,
            implementation=skill.implementation,
            existing_tests=skill.test_suite,
        )
        model = self.llm_router.get_model("adversarial") if self.llm_router else self.model
        adv_tests = llm_call(
            [{"role": "user", "content": prompt}],
            model=model,
        )
        adv_tests = adv_tests.strip()
        if adv_tests.startswith("```"):
            lines = adv_tests.split("\n")
            adv_tests = "\n".join(l for l in lines[1:] if l.strip() != "```")

        # Create a skill copy with combined tests
        combined = Skill(
            name=skill.name,
            implementation=skill.implementation,
            test_suite=skill.test_suite + "\n\n" + adv_tests,
        )
        result = self.sandbox.test_skill(combined)
        if result.success:
            # Merge adversarial tests into the skill's test suite
            skill.test_suite = combined.test_suite
            return True, ""
        else:
            failures = "\n".join(
                f"{t.test_name}: {t.error}" for t in result.test_results if not t.passed
            )
            return False, failures

    def generate_tests(self, skill: Skill, num_tests: int = 5) -> str:
        prompt = TEST_GENERATION_PROMPT.format(
            name=skill.name,
            description=skill.description,
            implementation=skill.implementation,
            num_tests=num_tests,
        )

        model = self.llm_router.get_model("test_generation") if self.llm_router else self.model
        return llm_call(
            [{"role": "user", "content": prompt}],
            model=model,
        )
