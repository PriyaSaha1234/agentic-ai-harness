# ============================================================
# TASK PLANNER
# ============================================================


class TaskPlanner:

    def __init__(self):

        self.current_task = None

        self.steps = []

        self.completed_steps = []


    # ========================================================
    # CREATE PLAN
    # ========================================================

    def create_plan(
        self,
        task: str,
        steps: str,
    ) -> str:

        try:

            parsed_steps = [
                step.strip()
                for step in steps.split("\n")
                if step.strip()
            ]

            if not parsed_steps:

                return (
                    "Planning failed: "
                    "No steps were provided."
                )

            self.current_task = task

            self.steps = parsed_steps

            self.completed_steps = []

            print(
                "\n[Planner] Created execution plan:"
            )

            for index, step in enumerate(
                self.steps,
                start=1,
            ):

                print(
                    f"  {index}. {step}"
                )

            return (
                f"Plan created successfully "
                f"with {len(self.steps)} steps."
            )

        except Exception as e:

            return f"Planning error: {e}"


    # ========================================================
    # COMPLETE STEP
    # ========================================================

    def complete_step(
        self,
        step_number: int,
    ) -> str:

        try:

            if not self.steps:

                return "No active plan."

            if (
                step_number < 1
                or step_number > len(self.steps)
            ):

                return "Invalid step number."

            if step_number in self.completed_steps:

                return (
                    f"Step {step_number} "
                    "is already completed."
                )

            self.completed_steps.append(
                step_number
            )

            step = self.steps[
                step_number - 1
            ]

            print(
                f"\n[Planner] Completed step "
                f"{step_number}: {step}"
            )

            return (
                f"Step {step_number} completed."
            )

        except Exception as e:

            return (
                f"Plan tracking error: {e}"
            )


    # ========================================================
    # PLAN STATUS
    # ========================================================

    def get_status(self) -> str:

        if not self.steps:

            return "No active plan."

        lines = [
            f"Task: {self.current_task}",
            "",
            "Plan:",
        ]

        for index, step in enumerate(
            self.steps,
            start=1,
        ):

            status = (
                "DONE"
                if index in self.completed_steps
                else "PENDING"
            )

            lines.append(
                f"{index}. [{status}] {step}"
            )

        return "\n".join(lines)


planner = TaskPlanner()