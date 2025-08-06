from django.utils.html import escape
from django.utils.text import slugify


def render_dynamic_form(fields, prefix="field"):
    html = ""
    for i, field in enumerate(fields):
        name = f"{prefix}_{slugify(field['label'])}_{i}"
        label = escape(field["label"])
        required = "required" if field.get("required") else ""

        ftype = field["field_type"]
        choices = field.get("choices", "")

        if ftype == "text":
            html += f'<label>{label}: <input type="text" name="{name}" {required}></label><br>'
        elif ftype == "textarea":
            html += f'<label>{label}: <textarea name="{name}" {required}></textarea></label><br>'
        elif ftype == "email":
            html += f'<label>{label}: <input type="email" name="{name}" {required}></label><br>'
        elif ftype == "number":
            html += f'<label>{label}: <input type="number" name="{name}" {required}></label><br>'
        elif ftype == "date":
            html += f'<label>{label}: <input type="date" name="{name}" {required}></label><br>'
        elif ftype == "time":
            html += f'<label>{label}: <input type="time" name="{name}" {required}></label><br>'
        elif ftype == "datetime":
            html += f'<label>{label}: <input type="datetime-local" name="{name}" {required}></label><br>'
        elif ftype == "range_date":
            html += f'<label>{label} (Start): <input type="date" name="{name}_start" {required}></label>'
            html += f'<label>{label} (End): <input type="date" name="{name}_end" {required}></label><br>'
        elif ftype == "range_time":
            html += f'<label>{label} (Start): <input type="time" name="{name}_start" {required}></label>'
            html += f'<label>{label} (End): <input type="time" name="{name}_end" {required}></label><br>'
        elif ftype == "range_datetime":
            html += f'<label>{label} (Start): <input type="datetime-local" name="{name}_start" {required}></label>'
            html += f'<label>{label} (End): <input type="datetime-local" name="{name}_end" {required}></label><br>'
        elif ftype == "choice":
            html += f'<label>{label}: <select name="{name}" {required}>'
            for opt in choices.split(","):
                html += f'<option value="{opt.strip()}">{opt.strip()}</option>'
            html += '</select></label><br>'
        elif ftype == "multi_choice":
            html += f'<label>{label}: <select name="{name}" multiple {required}>'
            for opt in choices.split(","):
                html += f'<option value="{opt.strip()}">{opt.strip()}</option>'
            html += '</select></label><br>'
        elif ftype == "checkbox":
            html += f'<label><input type="checkbox" name="{name}"> {label}</label><br>'
        elif ftype == "html_note":
            html += f'<div><em>{label}</em></div>'
        elif ftype == "section_heading":
            html += f'<h3>{label}</h3>'
        else:
            html += f'<label>{label}: <input type="text" name="{name}" {required}></label><br>'

    return html
