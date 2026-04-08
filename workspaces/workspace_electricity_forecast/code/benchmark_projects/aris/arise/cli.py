from __future__ import annotations

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(prog="arise", description="ARISE — Self-Evolving Agent Framework")
    sub = parser.add_subparsers(dest="command")

    # status
    p_status = sub.add_parser("status", help="Show library statistics")
    p_status.add_argument("path", nargs="?", default="./arise_skills", help="Skill library path")

    # skills
    p_skills = sub.add_parser("skills", help="List active skills")
    p_skills.add_argument("path", nargs="?", default="./arise_skills", help="Skill library path")

    # inspect
    p_inspect = sub.add_parser("inspect", help="Inspect a skill")
    p_inspect.add_argument("path", help="Skill library path")
    p_inspect.add_argument("skill_id", help="Skill ID")

    # rollback
    p_rollback = sub.add_parser("rollback", help="Rollback to a version")
    p_rollback.add_argument("path", help="Skill library path")
    p_rollback.add_argument("version", type=int, help="Version number")

    # export
    p_export = sub.add_parser("export", help="Export skills as .py files")
    p_export.add_argument("path", help="Skill library path")
    p_export.add_argument("output", help="Output directory")

    # dashboard
    p_dash = sub.add_parser("dashboard", help="Interactive dashboard")
    p_dash.add_argument("path", nargs="?", default="./arise_skills", help="Skill library path")
    p_dash.add_argument("--trajectories-path", default="./arise_trajectories", help="Trajectory store path")
    p_dash.add_argument("--web", action="store_true", help="Launch web UI instead of TUI")
    p_dash.add_argument("--port", type=int, default=8501, help="Web UI port")

    # registry
    p_registry = sub.add_parser("registry", help="Registry operations (export, import, search)")
    reg_sub = p_registry.add_subparsers(dest="registry_command")

    p_reg_export = reg_sub.add_parser("export", help="Export active skills to JSON")
    p_reg_export.add_argument("path", help="Skill library path")
    p_reg_export.add_argument("-o", "--output", default="skills.json", help="Output JSON file")

    p_reg_import = reg_sub.add_parser("import", help="Import skills from JSON")
    p_reg_import.add_argument("input", help="Input JSON file")
    p_reg_import.add_argument("path", help="Skill library path")

    p_reg_search = reg_sub.add_parser("search", help="Search skills in a library")
    p_reg_search.add_argument("query", help="Search query")
    p_reg_search.add_argument("--tags", nargs="*", help="Filter by tags")

    # history
    p_history = sub.add_parser("history", help="Show trajectory history")
    p_history.add_argument("path", nargs="?", default="./arise_trajectories", help="Trajectory store path")
    p_history.add_argument("-n", type=int, default=10, help="Number of entries")

    # setup-distributed
    p_setup = sub.add_parser("setup-distributed", help="Provision AWS resources for distributed ARISE")
    p_setup.add_argument("--region", default="us-west-2", help="AWS region")
    p_setup.add_argument("--bucket", default=None, help="S3 bucket name (auto-generated if omitted)")
    p_setup.add_argument("--queue", default=None, help="SQS queue name (auto-generated if omitted)")
    p_setup.add_argument("--profile", default=None, help="AWS profile")
    p_setup.add_argument("--destroy", action="store_true", help="Destroy resources from .arise.json")

    # evolve (dry-run)
    p_evolve = sub.add_parser("evolve", help="Trigger or preview evolution")
    p_evolve.add_argument("--skills-path", default="./arise_skills", help="Skill library path")
    p_evolve.add_argument("--trajectories-path", default="./arise_trajectories", help="Trajectory store path")
    p_evolve.add_argument("--dry-run", action="store_true", help="Show what would be created without calling LLM")

    # console
    p_console = sub.add_parser("console", help="Launch ARISE Console (web UI)")
    p_console.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    p_console.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_console.add_argument("--data-dir", default="~/.arise/console", help="Data directory")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "console":
        from arise.console.server import run_console
        run_console(data_dir=args.data_dir, port=args.port, host=args.host)

    elif args.command == "dashboard":
        if args.web:
            from arise.dashboard.web import run_web
            run_web(args.path, args.trajectories_path, port=args.port)
        else:
            from arise.dashboard.tui import run_tui
            run_tui(args.path, args.trajectories_path)

    elif args.command == "status":
        from arise.skills.library import SkillLibrary
        lib = SkillLibrary(args.path)
        stats = lib.stats()
        print(f"ARISE Skill Library — {args.path}")
        print(f"  Version:      {stats['library_version']}")
        print(f"  Active:       {stats['active']}")
        print(f"  Testing:      {stats['testing']}")
        print(f"  Deprecated:   {stats['deprecated']}")
        print(f"  Total:        {stats['total_skills']}")
        print(f"  Avg Success:  {stats['avg_success_rate']:.1%}")
        if stats["top_performers"]:
            print("\n  Top Performers:")
            for t in stats["top_performers"]:
                print(f"    {t['name']}: {t['success_rate']:.1%} ({t['invocations']} invocations)")

    elif args.command == "skills":
        from arise.skills.library import SkillLibrary
        lib = SkillLibrary(args.path)
        skills = lib.get_active_skills()
        if not skills:
            print("No active skills.")
            return
        print(f"{'Name':<25} {'Success':<10} {'Invocations':<12} {'Origin':<12} {'ID'}")
        print("-" * 75)
        for s in skills:
            print(f"{s.name:<25} {s.success_rate:<10.1%} {s.invocation_count:<12} {s.origin.value:<12} {s.id}")

    elif args.command == "inspect":
        from arise.skills.library import SkillLibrary
        lib = SkillLibrary(args.path)
        skill = lib.get_skill(args.skill_id)
        if skill is None:
            print(f"Skill {args.skill_id} not found.")
            sys.exit(1)
        print(f"Name:        {skill.name}")
        print(f"ID:          {skill.id}")
        print(f"Status:      {skill.status.value}")
        print(f"Origin:      {skill.origin.value}")
        print(f"Version:     {skill.version}")
        print(f"Success:     {skill.success_rate:.1%} ({skill.invocation_count} invocations)")
        print(f"Description: {skill.description}")
        print(f"\n--- Implementation ---\n{skill.implementation}")
        if skill.test_suite:
            print(f"\n--- Test Suite ---\n{skill.test_suite}")

    elif args.command == "rollback":
        from arise.skills.library import SkillLibrary
        lib = SkillLibrary(args.path)
        lib.rollback(args.version)
        print(f"Rolled back to version {args.version}.")

    elif args.command == "export":
        import os
        from arise.skills.library import SkillLibrary
        lib = SkillLibrary(args.path)
        os.makedirs(args.output, exist_ok=True)
        skills = lib.get_active_skills()
        for skill in skills:
            content = lib.export_skill(skill.id)
            filepath = os.path.join(args.output, f"{skill.name}.py")
            with open(filepath, "w") as f:
                f.write(content)
            print(f"Exported: {filepath}")
        print(f"\n{len(skills)} skills exported.")

    elif args.command == "setup-distributed":
        from arise.distributed import setup_distributed, destroy_distributed
        from arise.config import ARISEConfig

        if args.destroy:
            config_path = ".arise.json"
            try:
                with open(config_path) as f:
                    data = json.load(f)
            except FileNotFoundError:
                print("No .arise.json found. Nothing to destroy.")
                sys.exit(1)
            config = ARISEConfig(
                s3_bucket=data.get("s3_bucket"),
                sqs_queue_url=data.get("sqs_queue_url"),
                aws_region=data.get("aws_region", "us-east-1"),
            )
            destroy_distributed(config)
            import os
            os.remove(config_path)
            print("Removed .arise.json")
        else:
            config = setup_distributed(
                region=args.region,
                bucket_name=args.bucket,
                queue_name=args.queue,
                profile=args.profile,
            )
            data = {
                "s3_bucket": config.s3_bucket,
                "sqs_queue_url": config.sqs_queue_url,
                "aws_region": config.aws_region,
            }
            with open(".arise.json", "w") as f:
                json.dump(data, f, indent=2)
            print("Config saved to .arise.json")

    elif args.command == "evolve":
        from arise.skills.library import SkillLibrary
        from arise.skills.triggers import EvolutionTrigger
        from arise.trajectory.store import TrajectoryStore
        from arise.config import ARISEConfig

        lib = SkillLibrary(args.skills_path)
        store = TrajectoryStore(args.trajectories_path)
        config = ARISEConfig()
        trigger = EvolutionTrigger(config)

        recent = store.get_recent(config.plateau_window)
        should = trigger.should_evolve(recent, lib)
        print(f"Should evolve: {should}")

        failures = store.get_failures(n=config.failure_threshold * 2)
        print(f"Recent failures: {len(failures)}")

        if failures:
            patterns = trigger.get_failure_patterns(failures)
            if patterns:
                print("\nFailure patterns:")
                for p in patterns:
                    print(f"  [{p['count']}x] {p['error_pattern'][:80]}")
                    for task in p["example_tasks"][:2]:
                        print(f"       Task: {task[:60]}")

        if args.dry_run:
            if not failures:
                print("\n[DRY RUN] No failures to analyze — nothing to evolve.")
            else:
                from arise.skills.forge import SkillForge
                from arise.skills.sandbox import Sandbox
                sandbox = Sandbox(backend="subprocess", timeout=30)
                forge = SkillForge(model=config.model, sandbox=sandbox)
                print("\n[DRY RUN] Running gap detection (1 LLM call)...")
                gaps = forge.detect_gaps(failures, lib)
                if gaps:
                    active_names = {s.name for s in lib.get_active_skills()}
                    print(f"\nDetected {len(gaps)} capability gaps:")
                    for g in gaps:
                        exists = " (already exists)" if g.suggested_name in active_names else ""
                        print(f"  - {g.suggested_name}: {g.description}{exists}")
                        print(f"    Signature: {g.suggested_signature}")
                        if g.evidence:
                            for e in g.evidence[:2]:
                                print(f"    Evidence: {e[:80]}")
                    print("\nRun without --dry-run to synthesize these tools.")
                else:
                    print("\n[DRY RUN] No capability gaps detected.")
        else:
            print("\nUse --dry-run to preview, or run evolve() from Python to execute.")

    elif args.command == "registry":
        from arise.skills.library import SkillLibrary
        from arise.registry.client import export_skills, import_skills

        if args.registry_command == "export":
            lib = SkillLibrary(args.path)
            count = export_skills(lib, args.output)
            print(f"Exported {count} skills to {args.output}")

        elif args.registry_command == "import":
            lib = SkillLibrary(args.path)
            imported = import_skills(args.input, lib)
            print(f"Imported {len(imported)} skills into {args.path}")

        elif args.registry_command == "search":
            lib = SkillLibrary(args.path if hasattr(args, "path") else "./arise_skills")
            results = lib.search(args.query)
            if not results:
                print("No matching skills found.")
                return
            print(f"{'Name':<25} {'Success':<10} {'Invocations':<12} {'ID'}")
            print("-" * 60)
            for s in results:
                print(f"{s.name:<25} {s.success_rate:<10.1%} {s.invocation_count:<12} {s.id}")

        else:
            p_registry.print_help()

    elif args.command == "history":
        from arise.trajectory.store import TrajectoryStore
        store = TrajectoryStore(args.path)
        trajectories = store.get_recent(args.n)
        if not trajectories:
            print("No trajectories recorded.")
            return
        print(f"{'Task':<50} {'Reward':<8} {'Steps':<7} {'Time'}")
        print("-" * 85)
        for t in trajectories:
            task_short = t.task[:48] + ".." if len(t.task) > 48 else t.task
            print(f"{task_short:<50} {t.reward:<8.2f} {len(t.steps):<7} {t.timestamp.strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    main()
