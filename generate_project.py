import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export"

directories = [
    "config",
    "includes",
    "assets/css",
    "assets/js",
    "assets/images",
    "admin/products",
    "admin/suppliers",
    "admin/customers",
    "admin/imports",
    "admin/exports",
    "admin/inventory",
    "admin/invoices",
    "admin/reports",
    "admin/profile",
    "auth",
    "database",
]

for d in directories:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

print("Directories created successfully.")
