import os
import glob

def replace_in_file(filepath, old_text, new_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")

# Update port in config, agents, frontend pages, app
files_to_update = [
    'agentforge/config.py',
    'agentforge/agents/documentation_agent.py',
    'agentforge/frontend/pages/project_dashboard.py',
    'agentforge/frontend/pages/monitoring.py',
    'agentforge/frontend/pages/home.py',
    'agentforge/frontend/pages/history.py',
    'agentforge/frontend/pages/architecture.py',
    'agentforge/frontend/app.py',
    'agentforge/.env.example',
    'agentforge/.env'
]

for f in files_to_update:
    if os.path.exists(f):
        replace_in_file(f, '8000', '8001')

print("Port update script completed.")
