list-matrix-images:
    uv venv
    uv pip install -r requirements.txt
    uv run build_files/shared/list_images.py build_configurations.yaml