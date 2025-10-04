#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def build_variant(variant_name, i18n_file=None):
    """Build specific variant of the website"""
    
    # Use i18n_file parameter if provided, otherwise use variant_name
    i18n_name = i18n_file if i18n_file else variant_name.replace('-car', '')
    
    # Load i18n data for variant
    i18n_file_path = f"web/i18n/{i18n_name}.yaml"
    if not Path(i18n_file_path).exists():
        print(f"Error: {i18n_file_path} not found")
        sys.exit(1)
    
    with open(i18n_file_path, 'r', encoding='utf-8') as f:
        i18n_data = yaml.safe_load(f)
    
    # Load common i18n data
    common_path = "web/i18n/common.yaml"
    if Path(common_path).exists():
        with open(common_path, 'r', encoding='utf-8') as f:
            common_data = yaml.safe_load(f)
        build_data = {**common_data, **i18n_data}
    else:
        build_data = i18n_data
    
    # Create output directory
    output_dir = f"dist/{variant_name}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('web/templates'))
    
    # Build index.html with base path
    template = env.get_template('index.html')
    html_content = template.render(
        variant=variant_name,
        data=build_data,
        theme=os.getenv('THEME', variant_name),
        domain=os.getenv('DOMAIN', 'ai.sparetools.dev'),
        base_path=os.getenv('BASE_PATH', f'/{variant_name}')
    )
    
    with open(f"{output_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Copy CSS (variant-specific)
    css_source = f"web/css/{i18n_name}.css"
    if Path(css_source).exists():
        shutil.copy2(css_source, f"{output_dir}/style.css")
    elif Path("web/css/default.css").exists():
        shutil.copy2("web/css/default.css", f"{output_dir}/style.css")
    
    # Copy JavaScript
    if Path("web/js").exists():
        shutil.copytree("web/js", f"{output_dir}/js", dirs_exist_ok=True)
    
    print(f"✅ Built variant: {variant_name} (using i18n: {i18n_name})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_variant.py <variant_name> [i18n_file]")
        sys.exit(1)
    
    variant = sys.argv[1]
    i18n_file = sys.argv[2] if len(sys.argv) > 2 else None
    build_variant(variant, i18n_file)
