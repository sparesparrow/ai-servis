#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def build_variant(variant_name):
    """Build specific variant of the website"""
    
    # Load i18n data for variant
    i18n_file = f"web/i18n/{variant_name}.yaml"
    if not Path(i18n_file).exists():
        print(f"Error: {i18n_file} not found")
        sys.exit(1)
    
    with open(i18n_file, 'r', encoding='utf-8') as f:
        i18n_data = yaml.safe_load(f)
    
    # Load common i18n data
    with open("web/i18n/common.yaml", 'r', encoding='utf-8') as f:
        common_data = yaml.safe_load(f)
    
    # Merge data
    build_data = {**common_data, **i18n_data}
    
    # Create output directory
    output_dir = f"dist/{variant_name}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('web/templates'))
    
    # Build index.html
    template = env.get_template('index.html')
    html_content = template.render(
        variant=variant_name,
        data=build_data,
        theme=os.getenv('THEME', variant_name),
        domain=os.getenv('DOMAIN', f'{variant_name}.ai-servis.cz')
    )
    
    with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Copy CSS (variant-specific)
    css_source = f"web/css/{variant_name}.css"
    if Path(css_source).exists():
        shutil.copy2(css_source, f"{output_dir}/style.css")
    else:
        shutil.copy2("web/css/default.css", f"{output_dir}/style.css")
    
    # Copy JavaScript
    if Path("web/js").exists():
        shutil.copytree("web/js", f"{output_dir}/js", dirs_exist_ok=True)
    
    print(f"✅ Built variant: {variant_name}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_variant.py <variant_name>")
        sys.exit(1)
    
    variant = sys.argv[1]
    build_variant(variant)
