import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"

entities = {
    "products": {
        "table": "products",
        "singular": "Product",
        "singular_lower": "product",
        "plural": "Products",
        "code_field": "product_code",
        "name_field": "product_name",
        "fields": ["product_code", "product_name", "category", "unit", "price", "reorder_level", "status"]
    },
    "suppliers": {
        "table": "suppliers",
        "singular": "Supplier",
        "singular_lower": "supplier",
        "plural": "Suppliers",
        "code_field": "supplier_code",
        "name_field": "company_name",
        "fields": ["supplier_code", "company_name", "contact_person", "email", "phone", "country", "status"]
    },
    "customers": {
        "table": "customers",
        "singular": "Customer",
        "singular_lower": "customer",
        "plural": "Customers",
        "code_field": "customer_code",
        "name_field": "company_name",
        "fields": ["customer_code", "company_name", "contact_person", "email", "phone", "country", "status"]
    }
}

index_template = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$search = isset($_GET['search']) ? $_GET['search'] : '';
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$limit = 10;
$offset = ($page - 1) * $limit;

$query = "SELECT * FROM {table} WHERE {name_field} LIKE :search OR {code_field} LIKE :search ORDER BY id DESC LIMIT :limit OFFSET :offset";
$stmt = $conn->prepare($query);
$search_param = "%$search%";
$stmt->bindParam(':search', $search_param, PDO::PARAM_STR);
$stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
$stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
$stmt->execute();
$items = $stmt->fetchAll(PDO::FETCH_ASSOC);

$count_query = "SELECT COUNT(*) FROM {table} WHERE {name_field} LIKE :search OR {code_field} LIKE :search";
$count_stmt = $conn->prepare($count_query);
$count_stmt->execute(['search' => $search_param]);
$total_items = $count_stmt->fetchColumn();
$total_pages = ceil($total_items / $limit);

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">{plural}</h2>
    <a href="add.php" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> Add {singular}</a>
</div>

<?php if ($msg = displayFlashMessage('success')): ?>
    <div class="alert alert-success"><?php echo $msg; ?></div>
<?php endif; ?>

<div class="card shadow-sm mb-4">
    <div class="card-header bg-white py-3">
        <form class="d-flex align-items-center" method="GET">
            <input type="text" name="search" class="form-control me-2" placeholder="Search by name or code..." value="<?php echo htmlspecialchars($search); ?>">
            <button class="btn btn-outline-secondary" type="submit">Search</button>
        </form>
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (count($items) > 0): ?>
                        <?php foreach($items as $item): ?>
                        <tr>
                            <td><?php echo htmlspecialchars($item['{code_field}']); ?></td>
                            <td><?php echo htmlspecialchars($item['{name_field}']); ?></td>
                            <td>
                                <?php if($item['status'] == 'active'): ?>
                                    <span class="badge bg-success">Active</span>
                                <?php else: ?>
                                    <span class="badge bg-secondary">Inactive</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <a href="edit.php?id=<?php echo $item['id']; ?>" class="btn btn-sm btn-outline-primary"><i class="bi bi-pencil"></i> Edit</a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <tr><td colspan="4" class="text-center py-4">No {singular_lower}s found.</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
    <?php if ($total_pages > 1): ?>
    <div class="card-footer bg-white py-3">
        <nav>
            <ul class="pagination pagination-sm mb-0 justify-content-center">
                <?php for($i = 1; $i <= $total_pages; $i++): ?>
                    <li class="page-item <?php echo $page == $i ? 'active' : ''; ?>">
                        <a class="page-link" href="?page=<?php echo $i; ?>&search=<?php echo urlencode($search); ?>"><?php echo $i; ?></a>
                    </li>
                <?php endfor; ?>
            </ul>
        </nav>
    </div>
    <?php endif; ?>
</div>

<?php include '../../includes/footer.php'; ?>
"""

for entity, config in entities.items():
    folder = os.path.join(base_dir, entity)
    os.makedirs(folder, exist_ok=True)
    
    # Write index.php
    with open(os.path.join(folder, 'index.php'), 'w', encoding='utf-8') as f:
        f.write(index_template.format(**config))

print("Basic index files for Products, Suppliers, Customers generated.")
