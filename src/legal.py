import os
from jinja2 import Environment, FileSystemLoader

class LegalEngine:
    def __init__(self, templates_dir="templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def draft_email(self, target_data: dict, exposure: dict, enforcement: dict) -> str:
        template_name = "ccpa_request.j2" if exposure["type"] == "data_broker" else "dmca_takedown.j2"
        template = self.env.get_template(template_name)
        
        context = {**target_data, **exposure, **enforcement}
        return template.render(context)

    def send_email(self, content: str):
        # Mock SMTP sending for MVP
        print("\n--- DISPATCHING LEGAL NOTICE ---")
        print(content)
        print("--------------------------------\n")
        return True
