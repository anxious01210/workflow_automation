from django.shortcuts import render, get_object_or_404
from .models import *
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect


# Create your views here.

@csrf_exempt
def workflow_builder(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)

    if request.method == "POST":
        step_data_raw = request.POST.get("step_data", "").strip()
        step_configs_raw = request.POST.get("step_configs", "").strip()

        # ✅ Ensure valid JSON or fallback
        try:
            step_data = json.loads(step_data_raw) if step_data_raw else []
        except json.JSONDecodeError:
            step_data = []

        try:
            step_configs = json.loads(step_configs_raw) if step_configs_raw else {}
        except json.JSONDecodeError:
            step_configs = {}

        # Delete previous steps (optional - for reset)
        workflow.steps.all().delete()

        # Create new steps
        for i, step in enumerate(step_data):
            step_id = str(step.get("id") or i)
            config = step_configs.get(step_id, {})
            WorkflowStep.objects.create(
                workflow=workflow,
                name=step["name"],
                step_type=step["type"],
                order=step["order"],
                config=config
            )

        return redirect('core:workflow_builder', workflow_id=workflow.id)

    return render(request, 'core/workflow_builder.html', {
        'workflow': workflow,
        'step_configs_json': json.dumps({
            str(step.id): step.config for step in workflow.steps.all()
        })
    })
