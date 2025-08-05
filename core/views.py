# core/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Workflow, WorkflowStep
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin import site as admin_site


# ✅ Summary Table
# Request Type	What Happens
# GET	Django renders the HTML page with existing workflow data
# POST + JSON	Django saves the updated steps and responds with success/error JSON
# Other	Falls back to the render() (same as GET)
# @csrf_exempt  # 🔁 for testing only; prefer csrf_protect with fetch
@staff_member_required
def workflow_builder(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)

    if request.method == "POST" and request.content_type == "application/json":
        try:
            data = json.loads(
                request.body)  # Read the raw request body (because it’s JSON) & Convert the JSON string into a Python dictionary
            # Dictionary method get the "steps" if None then set the default to be [] instead of None.
            # These come from the frontend fetch() call:
            # body: JSON.stringify({ steps: steps, configs: allConfigs })
            steps = data.get("steps", [])
            configs = data.get("configs", {})

            # Delete all previous steps linked to this workflow & You’re rebuilding from scratch every time you save
            workflow.steps.all().delete()
            # Loop through each step submitted from the frontend
            # Convert the step ID to string (in case it's a number)
            # Create new step in the database for each one
            # Link it to the correct workflow
            # Pull the config dictionary from configs using the same step_id
            for step in steps:
                sid = str(step.get("id"))
                WorkflowStep.objects.create(
                    workflow=workflow,
                    name=step["name"],
                    step_type=step["type"],
                    order=step["order"],
                    config=configs.get(sid, {})
                )

            # Send back a success message to the front-end
            # The front-end then shows your toast/notification
            return JsonResponse({"success": True})
        # If anything goes wrong, return an error with the reason
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    # This happens when:
    #     You first open the page (GET)
    #     Or you refresh it
    #     Or any browser navigation request (not via fetch())
    # It does 3 things:
    #     Loads the template: workflow_builder.html
    #     Sends the current workflow object (so you can display its name, ID, etc.)
    #     Sends a JSON of all step configs (step_configs_json) so your JavaScript can populate modals and defaults
    # That’s why your JS has this:
    #     allConfigs = {{ step_configs_json|safe }};
    # ✅ Admin context
    context = admin_site.each_context(request)
    context.update({
        "workflow": workflow,
        "step_configs_json": json.dumps({
            str(step.id): step.config for step in workflow.steps.all()
        })
    })
    return render(request, 'core/workflow_builder.html', context)
