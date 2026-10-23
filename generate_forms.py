import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"

entities = {
    "products": {
        "table": "products",
        "singular": "Product",
        "singular_lower": "product",
        "code_field": "product_code",
        "name_field": "product_name",
        "form_fields": [
            ("product_code", "Product Code", "text", True),
            ("product_name", "Product Name", "text", True),
            ("category", "Category", "text", True),
            ("description", "Description", "textarea", False),
            ("unit", "Unit", "text", True),
            ("price", "Price", "number", True),
            ("reorder_level", "Reorder Level", "number", True),
            ("status", "Status", "select", True)
        ]
    },
    "suppliers": {
        "table": "suppliers",
        "singular": "Supplier",
        "singular_lower": "supplier",
        "code_field": "supplier_code",
        "name_field": "company_name",
        "form_fields": [
            ("supplier_code", "Supplier Code", "text", True),
            ("company_name", "Company Name", "text", True),
            ("contact_person", "Contact Person", "text", False),
            ("email", "Email", "email", False),
            ("phone", "Phone", "text", False),
            ("address", "Address", "textarea", False),
            ("city", "City", "text", False),
            ("country", "Country", "text", False),
            ("status", "Status", "select", True)
        ]
    },
    "customers": {
        "table": "customers",
        "singular": "Customer",
        "singular_lower": "customer",
        "code_field": "customer_code",
        "name_field": "company_name",
        "form_fields": [
            ("customer_code", "Customer Code", "text", True),
            ("company_name", "Company Name", "text", True),
            ("contact_person", "Contact Person", "text", False),
            ("email", "Email", "email", False),
            ("phone", "Phone", "text", False),
            ("address", "Address", "textarea", False),
            ("city", "City", "text", False),
            ("country", "Country", "text", False),
            ("status", "Status", "select", True)
        ]
    }
}

add_template = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$error = '';

if ($_SERVER['REQUEST_METHOD'] == 'POST') {{
    {post_vars}
    
    // Check if code exists
    $stmt = $conn->prepare("SELECT id FROM {table} WHERE {code_field} = ?");
    $stmt->execute([${code_field}]);
    if ($stmt->rowCount() > 0) {{
        $error = '{code_field_title} already exists.';
    }} else {{
        $query = "INSERT INTO {table} ({insert_fields}) VALUES ({insert_placeholders})";
        $stmt = $conn->prepare($query);
        if ($stmt->execute([{execute_vars}])) {{
            {after_insert}
            setFlashMessage('success', '{singular} added successfully.');
            redirect('/jupiter-import-export/admin/{folder}/index.php');
        }} else {{
            $error = 'Failed to add {singular_lower}.';
        }}
    }}
}}

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Add {singular}</h2>
    <a href="index.php" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> Back</a>
</div>

<?php if ($error): ?>
    <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
<?php endif; ?>

<div class="card shadow-sm">
    <div class="card-body">
        <form method="POST" action="">
            <div class="row">
{form_html}
            </div>
            <hr>
            <button type="submit" class="btn btn-primary">Save {singular}</button>
        </form>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

edit_template = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

if (!isset($_GET['id'])) {{
    redirect('/jupiter-import-export/admin/{folder}/index.php');
}}

$id = (int)$_GET['id'];
$error = '';

$stmt = $conn->prepare("SELECT * FROM {table} WHERE id = ?");
$stmt->execute([$id]);
$item = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$item) {{
    redirect('/jupiter-import-export/admin/{folder}/index.php');
}}

if ($_SERVER['REQUEST_METHOD'] == 'POST') {{
    {post_vars}
    
    // Check if code exists for another ID
    $stmt = $conn->prepare("SELECT id FROM {table} WHERE {code_field} = ? AND id != ?");
    $stmt->execute([${code_field}, $id]);
    if ($stmt->rowCount() > 0) {{
        $error = '{code_field_title} already exists.';
    }} else {{
        $query = "UPDATE {table} SET {update_fields} WHERE id = ?";
        $stmt = $conn->prepare($query);
        $exec_vars = [{execute_vars}, $id];
        if ($stmt->execute($exec_vars)) {{
            setFlashMessage('success', '{singular} updated successfully.');
            redirect('/jupiter-import-export/admin/{folder}/index.php');
        }} else {{
            $error = 'Failed to update {singular_lower}.';
        }}
    }}
}}

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Edit {singular}</h2>
    <a href="index.php" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> Back</a>
</div>

<?php if ($error): ?>
    <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
<?php endif; ?>

<div class="card shadow-sm">
    <div class="card-body">
        <form method="POST" action="">
            <div class="row">
{edit_form_html}
            </div>
            <hr>
            <button type="submit" class="btn btn-primary">Update {singular}</button>
        </form>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

for entity, config in entities.items():
    folder = os.path.join(base_dir, entity)
    
    post_vars = []
    insert_fields = []
    insert_placeholders = []
    execute_vars = []
    update_fields = []
    
    form_html = ""
    edit_form_html = ""
    
    for field, title, ftype, req in config['form_fields']:
        post_vars.append(f"${field} = trim($_POST['{field}']);")
        insert_fields.append(field)
        insert_placeholders.append("?")
        execute_vars.append(f"${field}")
        update_fields.append(f"{field} = ?")
        
        req_attr = "required" if req else ""
        req_star = "<span class='text-danger'>*</span>" if req else ""
        
        # Add form HTML
        col_class = "col-md-12" if ftype == 'textarea' else "col-md-6"
        
        input_html = ""
        edit_input_html = ""
        
        if ftype == 'textarea':
            input_html = f'<textarea name="{field}" class="form-control" {req_attr}></textarea>'
            edit_input_html = f'<textarea name="{field}" class="form-control" {req_attr}><?php echo htmlspecialchars($item["{field}"]); ?></textarea>'
        elif ftype == 'select' and field == 'status':
            input_html = f"""<select name="{field}" class="form-select" {req_attr}>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
            </select>"""
            edit_input_html = f"""<select name="{field}" class="form-select" {req_attr}>
                <option value="active" <?php echo $item["{field}"] == 'active' ? 'selected' : ''; ?>>Active</option>
                <option value="inactive" <?php echo $item["{field}"] == 'inactive' ? 'selected' : ''; ?>>Inactive</option>
            </select>"""
        else:
            step = 'step="0.01"' if ftype == 'number' else ''
            input_html = f'<input type="{ftype}" name="{field}" class="form-control" {req_attr} {step}>'
            edit_input_html = f'<input type="{ftype}" name="{field}" class="form-control" {req_attr} {step} value="<?php echo htmlspecialchars($item["{field}"]); ?>">'
            
        form_html += f"""
                <div class="{col_class} mb-3">
                    <label class="form-label">{title} {req_star}</label>
                    {input_html}
                </div>"""
                
        edit_form_html += f"""
                <div class="{col_class} mb-3">
                    <label class="form-label">{title} {req_star}</label>
                    {edit_input_html}
                </div>"""

    after_insert = ""
    if entity == "products":
        after_insert = """
            $product_id = $conn->lastInsertId();
            $stmt = $conn->prepare("INSERT INTO inventory (product_id, quantity, reserved_quantity, available_quantity) VALUES (?, 0, 0, 0)");
            $stmt->execute([$product_id]);
        """
        
    code_field_title = "Code"
    for f in config['form_fields']:
        if f[0] == config['code_field']:
            code_field_title = f[1]
            break

    # Write add.php
    with open(os.path.join(folder, 'add.php'), 'w', encoding='utf-8') as f:
        f.write(add_template.format(
            folder=entity,
            table=config['table'],
            singular=config['singular'],
            singular_lower=config['singular_lower'],
            code_field=config['code_field'],
            code_field_title=code_field_title,
            post_vars="\n    ".join(post_vars),
            insert_fields=", ".join(insert_fields),
            insert_placeholders=", ".join(insert_placeholders),
            execute_vars=", ".join(execute_vars),
            after_insert=after_insert,
            form_html=form_html
        ))

    # Write edit.php
    with open(os.path.join(folder, 'edit.php'), 'w', encoding='utf-8') as f:
        f.write(edit_template.format(
            folder=entity,
            table=config['table'],
            singular=config['singular'],
            singular_lower=config['singular_lower'],
            code_field=config['code_field'],
            code_field_title=code_field_title,
            post_vars="\n    ".join(post_vars),
            update_fields=", ".join(update_fields),
            execute_vars=", ".join(execute_vars),
            edit_form_html=edit_form_html
        ))

print("Add and Edit scripts for Products, Suppliers, Customers generated.")
