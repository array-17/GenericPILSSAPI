"""
Fork customization module (EDIT AT WILL).

Put all fork-specific metadata and class selections in this file.
`app.py` should remain stable and generally not require edits for normal forks.
"""


svc_name_ = "PILSSAppService"
svc_display_name_ = "PILSS Flask App Service"
svc_description_ = "Runs the PILSS Flask app as a Windows service."

from Pilss import PILSSAction, PILSSResults, PILSSOnBottomTemplate, PILSSSchemaTemplate, PILSSDownloadable

# API details for NautIQ discovery
API_META = {"name": "PILSSAPI", "version": "0.6"}

# Core runtime classes used by app.py
ACTION_CLASS = PILSSAction
RESULTS_CLASSES = [PILSSResults]
TEMPLATE_CLASSES = [PILSSOnBottomTemplate]
DOWNLOADABLE_CLASS = PILSSDownloadable


def validate_fork_config():
    if ACTION_CLASS is None:
        raise Exception("No ACTION_CLASS defined in fork_config.py")
    if not hasattr(ACTION_CLASS, "perform_action"):
        raise Exception("ACTION_CLASS does not have perform_action method defined")
    if not callable(getattr(ACTION_CLASS, "perform_action")):
        raise Exception("ACTION_CLASS.perform_action is not callable")

    if RESULTS_CLASSES is None or len(RESULTS_CLASSES) == 0:
        raise Exception("No RESULTS_CLASSES defined in fork_config.py")
    for result_class in RESULTS_CLASSES:
        if not hasattr(result_class, "process_results"):
            raise Exception(
                f"Results class {result_class.__name__} does not have process_results method defined"
            )
        if not callable(getattr(result_class, "process_results")):
            raise Exception(
                f"Results class {result_class.__name__}.process_results is not callable"
            )

    if TEMPLATE_CLASSES is None:
        raise Exception("TEMPLATE_CLASSES must be defined in fork_config.py")
    for template_class in TEMPLATE_CLASSES:
        has_old = hasattr(template_class, "toFrontend_parameters") and callable(
            getattr(template_class, "toFrontend_parameters")
        )
        has_new = hasattr(template_class, "to_frontend_parameters") and callable(
            getattr(template_class, "to_frontend_parameters")
        )
        if not (has_old or has_new):
            raise Exception(
                f"Template class {template_class.__name__} must define toFrontend_parameters or to_frontend_parameters"
            )

    if DOWNLOADABLE_CLASS is None:
        raise Exception("DOWNLOADABLE_CLASS must be defined in fork_config.py")
