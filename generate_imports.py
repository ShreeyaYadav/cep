import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"

# IMPORTS
imports_dir = os.path.join(base_dir, "imports")
os.makedirs(imports_dir, exist_ok=True)

imports_index = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$search = isset($_GET['search']) ? trim($_GET['search']) : '';
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$limit = 10;
$offset = ($page - 1) * $limit;

$query = "SELECT i.*, p.product_name, s.company_name as supplier_name 
          FROM imports i 
          JOIN products p ON i.product_id = p.id 
          JOIN suppliers s ON i.supplier_id = s.id 
          WHERE i.import_number LIKE :search OR s.company_name LIKE :search 
          ORDER BY i.id DESC LIMIT :limit OFFSET :offset";
$stmt = $conn->prepare($query);
$search_param = "%$search%";
$stmt->bindParam(':search', $search_param, PDO::PARAM_STR);
$stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
$stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
$stmt->execute();
$items = $stmt->fetchAll(PDO::FETCH_ASSOC);

$count_query = "SELECT COUNT(*) FROM imports i JOIN suppliers s ON i.supplier_id = s.id WHERE i.import_number LIKE :search OR s.company_name LIKE :search";
$count_stmt = $conn->prepare($count_query);
$count_stmt->execute(['search' => $search_param]);
$total_pages = ceil($count_stmt->fetchColumn() / $limit);

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Imports</h2>
    <a href="add.php" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> New Import</a>
</div>

<?php if ($msg = displayFlashMessage('success')): ?>
    <div class="alert alert-success"><?php echo $msg; ?></div>
<?php endif; ?>

<div class="card shadow-sm mb-4">
    <div class="card-header bg-white py-3">
        <form class="d-flex align-items-center" method="GET">
            <input type="text" name="search" class="form-control me-2" placeholder="Search by import number or supplier..." value="<?php echo htmlspecialchars($search); ?>">
            <button class="btn btn-outline-secondary" type="submit">Search</button>
        </form>
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Import No.</th>
                        <th>Date</th>
                        <th>Supplier</th>
                        <th>Product</th>
                        <th>Qty</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (count($items) > 0): ?>
                        <?php foreach($items as $item): ?>
                        <tr>
                            <td><?php echo htmlspecialchars($item['import_number']); ?></td>
                            <td><?php echo date('d M Y', strtotime($item['import_date'])); ?></td>
                            <td><?php echo htmlspecialchars($item['supplier_name']); ?></td>
                            <td><?php echo htmlspecialchars($item['product_name']); ?></td>
                            <td><?php echo $item['quantity']; ?></td>
                            <td>$<?php echo number_format($item['total_amount'], 2); ?></td>
                            <td>
                                <?php 
                                $bg = 'secondary';
                                if($item['status'] == 'Received') $bg = 'success';
                                elseif($item['status'] == 'In Transit') $bg = 'info';
                                elseif($item['status'] == 'Pending') $bg = 'warning text-dark';
                                elseif($item['status'] == 'Cancelled') $bg = 'danger';
                                ?>
                                <span class="badge bg-<?php echo $bg; ?>"><?php echo $item['status']; ?></span>
                            </td>
                            <td>
                                <a href="view.php?id=<?php echo $item['id']; ?>" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i> View</a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <tr><td colspan="8" class="text-center py-4">No imports found.</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

imports_add = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$error = '';

$suppliers = $conn->query("SELECT id, company_name FROM suppliers WHERE status = 'active'")->fetchAll(PDO::FETCH_ASSOC);
$products = $conn->query("SELECT id, product_name, price FROM products WHERE status = 'active'")->fetchAll(PDO::FETCH_ASSOC);

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $import_number = trim($_POST['import_number']);
    $supplier_id = (int)$_POST['supplier_id'];
    $import_date = $_POST['import_date'];
    $product_id = (int)$_POST['product_id'];
    $quantity = (int)$_POST['quantity'];
    $unit_cost = (float)$_POST['unit_cost'];
    $shipping_cost = (float)$_POST['shipping_cost'];
    $customs_cost = (float)$_POST['customs_cost'];
    $remarks = trim($_POST['remarks']);
    
    $total_amount = ($quantity * $unit_cost) + $shipping_cost + $customs_cost;
    
    // check unique
    $stmt = $conn->prepare("SELECT id FROM imports WHERE import_number = ?");
    $stmt->execute([$import_number]);
    if ($stmt->rowCount() > 0) {
        $error = 'Import Number already exists.';
    } elseif ($quantity <= 0) {
        $error = 'Quantity must be greater than zero.';
    } else {
        $query = "INSERT INTO imports (import_number, supplier_id, import_date, product_id, quantity, unit_cost, total_amount, shipping_cost, customs_cost, status, remarks, created_by) 
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)";
        $stmt = $conn->prepare($query);
        if ($stmt->execute([$import_number, $supplier_id, $import_date, $product_id, $quantity, $unit_cost, $total_amount, $shipping_cost, $customs_cost, $remarks, $_SESSION['user_id']])) {
            setFlashMessage('success', 'Import created successfully. Stock will update when status is Received.');
            redirect('/jupiter-import-export/admin/imports/index.php');
        } else {
            $error = 'Failed to create import.';
        }
    }
}

include '../../includes/header.php';
?>
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">New Import</h2>
    <a href="index.php" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> Back</a>
</div>

<?php if ($error): ?>
    <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
<?php endif; ?>

<div class="card shadow-sm">
    <div class="card-body">
        <form method="POST" action="">
            <div class="row">
                <div class="col-md-6 mb-3">
                    <label class="form-label">Import Number <span class="text-danger">*</span></label>
                    <input type="text" name="import_number" class="form-control" required value="IMP-<?php echo time(); ?>">
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Import Date <span class="text-danger">*</span></label>
                    <input type="date" name="import_date" class="form-control" required value="<?php echo date('Y-m-d'); ?>">
                </div>
                
                <div class="col-md-6 mb-3">
                    <label class="form-label">Supplier <span class="text-danger">*</span></label>
                    <select name="supplier_id" class="form-select" required>
                        <option value="">Select Supplier</option>
                        <?php foreach($suppliers as $s): ?>
                            <option value="<?php echo $s['id']; ?>"><?php echo htmlspecialchars($s['company_name']); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Product <span class="text-danger">*</span></label>
                    <select name="product_id" class="form-select" required>
                        <option value="">Select Product</option>
                        <?php foreach($products as $p): ?>
                            <option value="<?php echo $p['id']; ?>"><?php echo htmlspecialchars($p['product_name']); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <div class="col-md-3 mb-3">
                    <label class="form-label">Quantity <span class="text-danger">*</span></label>
                    <input type="number" name="quantity" class="form-control" required min="1">
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Unit Cost ($) <span class="text-danger">*</span></label>
                    <input type="number" name="unit_cost" step="0.01" class="form-control" required>
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Shipping Cost ($)</label>
                    <input type="number" name="shipping_cost" step="0.01" class="form-control" value="0">
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Customs Cost ($)</label>
                    <input type="number" name="customs_cost" step="0.01" class="form-control" value="0">
                </div>
                
                <div class="col-md-12 mb-3">
                    <label class="form-label">Remarks</label>
                    <textarea name="remarks" class="form-control" rows="2"></textarea>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Create Import</button>
        </form>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

imports_view = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

if (!isset($_GET['id'])) {
    redirect('/jupiter-import-export/admin/imports/index.php');
}

$id = (int)$_GET['id'];
$error = '';

$stmt = $conn->prepare("
    SELECT i.*, p.product_name, p.product_code, s.company_name, u.name as created_by_name 
    FROM imports i 
    JOIN products p ON i.product_id = p.id 
    JOIN suppliers s ON i.supplier_id = s.id 
    JOIN users u ON i.created_by = u.id 
    WHERE i.id = ?
");
$stmt->execute([$id]);
$import = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$import) {
    redirect('/jupiter-import-export/admin/imports/index.php');
}

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['update_status'])) {
    $new_status = $_POST['status'];
    if ($import['status'] != 'Received' && $import['status'] != 'Cancelled') {
        $stmt = $conn->prepare("UPDATE imports SET status = ? WHERE id = ?");
        
        if ($stmt->execute([$new_status, $id])) {
            // Inventory Logic!
            if ($new_status == 'Received') {
                updateInventoryOnImport($conn, $import['product_id'], $import['quantity']);
                
                // Fetch balance
                $bal_stmt = $conn->prepare("SELECT available_quantity FROM inventory WHERE product_id = ?");
                $bal_stmt->execute([$import['product_id']]);
                $balance = $bal_stmt->fetchColumn();
                
                recordInventoryTransaction($conn, $import['product_id'], 'IMPORT', $import['import_number'], $import['quantity'], $balance, $_SESSION['user_id']);
                setFlashMessage('success', 'Import marked as Received. Inventory has been updated.');
            } else {
                setFlashMessage('success', 'Import status updated.');
            }
            redirect('/jupiter-import-export/admin/imports/view.php?id=' . $id);
        }
    }
}

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Import Details: <?php echo htmlspecialchars($import['import_number']); ?></h2>
    <a href="index.php" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> Back</a>
</div>

<?php if ($msg = displayFlashMessage('success')): ?>
    <div class="alert alert-success"><?php echo $msg; ?></div>
<?php endif; ?>

<div class="row">
    <div class="col-md-8">
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white">
                <h6 class="mb-0">Transaction Information</h6>
            </div>
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Supplier</div>
                    <div class="col-sm-8 fw-bold"><?php echo htmlspecialchars($import['company_name']); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Date</div>
                    <div class="col-sm-8"><?php echo date('d M Y', strtotime($import['import_date'])); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Product</div>
                    <div class="col-sm-8"><?php echo htmlspecialchars($import['product_code'] . ' - ' . $import['product_name']); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Quantity</div>
                    <div class="col-sm-8"><?php echo $import['quantity']; ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Remarks</div>
                    <div class="col-sm-8"><?php echo nl2br(htmlspecialchars($import['remarks'])); ?></div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-white">
                <h6 class="mb-0">Financials & Status</h6>
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Unit Cost:</span>
                    <span>$<?php echo number_format($import['unit_cost'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Product Total:</span>
                    <span>$<?php echo number_format($import['quantity'] * $import['unit_cost'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Shipping:</span>
                    <span>$<?php echo number_format($import['shipping_cost'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Customs:</span>
                    <span>$<?php echo number_format($import['customs_cost'], 2); ?></span>
                </div>
                <hr>
                <div class="d-flex justify-content-between mb-3 fw-bold">
                    <span>Grand Total:</span>
                    <span class="text-primary">$<?php echo number_format($import['total_amount'], 2); ?></span>
                </div>
                
                <div class="mb-3">
                    <label class="text-muted mb-1 d-block">Current Status:</label>
                    <h5>
                        <?php 
                        $bg = 'secondary';
                        if($import['status'] == 'Received') $bg = 'success';
                        elseif($import['status'] == 'In Transit') $bg = 'info';
                        elseif($import['status'] == 'Pending') $bg = 'warning text-dark';
                        elseif($import['status'] == 'Cancelled') $bg = 'danger';
                        ?>
                        <span class="badge bg-<?php echo $bg; ?>"><?php echo $import['status']; ?></span>
                    </h5>
                </div>
                
                <?php if ($import['status'] == 'Pending' || $import['status'] == 'In Transit'): ?>
                <form method="POST" action="">
                    <input type="hidden" name="update_status" value="1">
                    <div class="mb-3">
                        <select name="status" class="form-select">
                            <option value="Pending" <?php echo $import['status'] == 'Pending' ? 'selected' : ''; ?>>Pending</option>
                            <option value="In Transit" <?php echo $import['status'] == 'In Transit' ? 'selected' : ''; ?>>In Transit</option>
                            <option value="Received">Received (Updates Inventory)</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Update Status</button>
                </form>
                <?php else: ?>
                    <div class="alert alert-light border">
                        Status is final. Cannot be changed.
                    </div>
                <?php endif; ?>
                
            </div>
        </div>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

with open(os.path.join(imports_dir, 'index.php'), 'w', encoding='utf-8') as f:
    f.write(imports_index)
with open(os.path.join(imports_dir, 'add.php'), 'w', encoding='utf-8') as f:
    f.write(imports_add)
with open(os.path.join(imports_dir, 'view.php'), 'w', encoding='utf-8') as f:
    f.write(imports_view)

print("Imports module generated.")
