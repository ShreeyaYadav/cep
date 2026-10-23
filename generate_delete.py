import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"

entities = ["products", "suppliers", "customers"]

delete_template = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

if (!isset($_GET['id'])) {{
    redirect('/jupiter-import-export/admin/{folder}/index.php');
}}

$id = (int)$_GET['id'];
$stmt = $conn->prepare("DELETE FROM {folder} WHERE id = ?");
try {{
    if ($stmt->execute([$id])) {{
        setFlashMessage('success', 'Record deleted successfully.');
    }} else {{
        setFlashMessage('error', 'Failed to delete record.');
    }}
}} catch (PDOException $e) {{
    setFlashMessage('error', 'Cannot delete this record because it is referenced in other transactions.');
}}
redirect('/jupiter-import-export/admin/{folder}/index.php');
?>
"""

for entity in entities:
    folder = os.path.join(base_dir, entity)
    # Write delete.php
    with open(os.path.join(folder, 'delete.php'), 'w', encoding='utf-8') as f:
        f.write(delete_template.format(folder=entity))

print("Delete scripts generated.")
