import os

folders = [
    "models",
    "widgets",
    "utils",
    "printing",
    "resources",
    "tests",
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    init_path = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w", encoding="utf-8") as f:
            f.write(f"# Plik inicjujący moduł {folder}\n")

print("Utworzono katalogi i pliki __init__.py.")