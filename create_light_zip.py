import os
import zipfile

root = os.getcwd()
output = r"E:\LedgerForge_Project\LedgerForge_Deploy.zip"

exclude_dirs = {
    ".git", ".venv", "venv", "__pycache__",
    ".pytest_cache", "node_modules",
    "task9_export", "task9_final_export",
    "task12_final_export"
}

exclude_files = {
    ".env",
    "ledgerforge.db",
    "task13_deactivation_test.db",
    "task12_paid_test.db",
    "task12_workflow_test.db",
    "task12_test.db",
}

with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as z:
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file in exclude_files or file.endswith((".pyc", ".db")):
                continue

            path = os.path.join(folder, file)
            arcname = os.path.relpath(path, root)
            z.write(path, arcname)

print("Lightweight deployment ZIP created:", output)
