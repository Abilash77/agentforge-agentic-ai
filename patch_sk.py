import os
import site

# Try user site packages first
user_site = site.getusersitepackages()
pydantic_file = os.path.join(user_site, 'semantic_kernel', 'sk_pydantic.py')

if not os.path.exists(pydantic_file):
    # Try global site packages
    for sp in site.getsitepackages():
        pydantic_file = os.path.join(sp, 'semantic_kernel', 'sk_pydantic.py')
        if os.path.exists(pydantic_file):
            break

print("Patching:", pydantic_file)

with open(pydantic_file, 'r') as f:
    content = f.read()
content = content.replace("from pydantic.networks import Url", "try:\n    from pydantic import AnyUrl as Url\nexcept ImportError:\n    from pydantic.networks import Url\n")
with open(pydantic_file, 'w') as f:
    f.write(content)
print("Patched sk_pydantic.py")
