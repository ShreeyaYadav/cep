import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"

# EXPORTS
exports_dir = os.path.join(base_dir, "exports")
os.makedirs(exports_dir, exist_ok=True)

exports_index = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$search = isset($_GET['search']) ? trim($_GET['search']) : '';
$page = isset($_GET['page']) ? (int)$_GET['page'] : 1;
$limit = 10;
$offset = ($page - 1) * $limit;

$query = "SELECT e.*, p.product_name, c.company_name as customer_name 
          FROM exports e 
          JOIN products p ON e.product_id = p.id 
          JOIN customers c ON e.customer_id = c.id 
          WHERE e.export_number LIKE :search OR c.company_name LIKE :search 
          ORDER BY e.id DESC LIMIT :limit OFFSET :offset";
$stmt = $conn->prepare($query);
$search_param = "%$search%";
$stmt->bindParam(':search', $search_param, PDO::PARAM_STR);
$stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
$stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
$stmt->execute();
$items = $stmt->fetchAll(PDO::FETCH_ASSOC);

$count_query = "SELECT COUNT(*) FROM exports e JOIN customers c ON e.customer_id = c.id WHERE e.export_number LIKE :search OR c.company_name LIKE :search";
$count_stmt = $conn->prepare($count_query);
$count_stmt->execute(['search' => $search_param]);
$total_pages = ceil($count_stmt->fetchColumn() / $limit);

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Exports</h2>
    <a href="add.php" class="btn btn-primary"><i class="bi bi-plus-circle me-1"></i> New Export</a>
</div>

<?php if ($msg = displayFlashMessage('success')): ?>
    <div class="alert alert-success"><?php echo $msg; ?></div>
<?php endif; ?>

<div class="card shadow-sm mb-4">
    <div class="card-header bg-white py-3">
        <form class="d-flex align-items-center" method="GET">
            <input type="text" name="search" class="form-control me-2" placeholder="Search by export number or customer..." value="<?php echo htmlspecialchars($search); ?>">
            <button class="btn btn-outline-secondary" type="submit">Search</button>
        </form>
    </div>
    <div class="card-body p-0">
        <div class="table-responsive">
            <table class="table table-hover mb-0">
                <thead class="table-light">
                    <tr>
                        <th>Export No.</th>
                        <th>Date</th>
                        <th>Customer</th>
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
                            <td><?php echo htmlspecialchars($item['export_number']); ?></td>
                            <td><?php echo date('d M Y', strtotime($item['export_date'])); ?></td>
                            <td><?php echo htmlspecialchars($item['customer_name']); ?></td>
                            <td><?php echo htmlspecialchars($item['product_name']); ?></td>
                            <td><?php echo $item['quantity']; ?></td>
                            <td>$<?php echo number_format($item['total_amount'], 2); ?></td>
                            <td>
                                <?php 
                                $bg = 'secondary';
                                if($item['status'] == 'Delivered') $bg = 'success';
                                elseif($item['status'] == 'Shipped') $bg = 'info';
                                elseif($item['status'] == 'Processing') $bg = 'primary';
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
                        <tr><td colspan="8" class="text-center py-4">No exports found.</td></tr>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</div>

<?php include '../../includes/footer.php'; ?>
"""

exports_add = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

$error = '';

$customers = $conn->query("SELECT id, company_name FROM customers WHERE status = 'active'")->fetchAll(PDO::FETCH_ASSOC);
$products = $conn->query("
    SELECT p.id, p.product_name, p.price, i.available_quantity 
    FROM products p 
    JOIN inventory i ON p.id = i.product_id 
    WHERE p.status = 'active'
")->fetchAll(PDO::FETCH_ASSOC);

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $export_number = trim($_POST['export_number']);
    $customer_id = (int)$_POST['customer_id'];
    $export_date = $_POST['export_date'];
    $product_id = (int)$_POST['product_id'];
    $quantity = (int)$_POST['quantity'];
    $unit_price = (float)$_POST['unit_price'];
    $shipping_cost = (float)$_POST['shipping_cost'];
    $tax = (float)$_POST['tax'];
    $remarks = trim($_POST['remarks']);
    
    $subtotal = $quantity * $unit_price;
    $total_amount = $subtotal + $shipping_cost + $tax;
    
    // Check inventory FIRST
    if (!validateStockForExport($conn, $product_id, $quantity)) {
        // Fetch current available stock
        $stmt_s = $conn->prepare("SELECT available_quantity FROM inventory WHERE product_id = ?");
        $stmt_s->execute([$product_id]);
        $avail = $stmt_s->fetchColumn();
        $error = "Insufficient stock. Available quantity: {$avail}.";
    } else {
        // check unique export number
        $stmt = $conn->prepare("SELECT id FROM exports WHERE export_number = ?");
        $stmt->execute([$export_number]);
        if ($stmt->rowCount() > 0) {
            $error = 'Export Number already exists.';
        } elseif ($quantity <= 0) {
            $error = 'Quantity must be greater than zero.';
        } else {
            // We will create the export as Processing directly to deduct stock immediately as requested
            $query = "INSERT INTO exports (export_number, customer_id, export_date, product_id, quantity, unit_price, total_amount, shipping_cost, tax, status, remarks, created_by) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Processing', ?, ?)";
            $stmt = $conn->prepare($query);
            
            $conn->beginTransaction();
            try {
                $stmt->execute([$export_number, $customer_id, $export_date, $product_id, $quantity, $unit_price, $total_amount, $shipping_cost, $tax, $remarks, $_SESSION['user_id']]);
                $export_id = $conn->lastInsertId();
                
                // Deduct stock
                updateInventoryOnExport($conn, $product_id, $quantity);
                
                // Fetch balance
                $bal_stmt = $conn->prepare("SELECT available_quantity FROM inventory WHERE product_id = ?");
                $bal_stmt->execute([$product_id]);
                $balance = $bal_stmt->fetchColumn();
                
                // Record transaction
                recordInventoryTransaction($conn, $product_id, 'EXPORT', $export_number, $quantity, $balance, $_SESSION['user_id']);
                
                // Automatically generate Invoice
                $invoice_number = 'INV-' . time();
                $inv_query = "INSERT INTO invoices (invoice_number, invoice_type, export_id, customer_id, invoice_date, subtotal, tax, shipping, grand_total) 
                              VALUES (?, 'EXPORT', ?, ?, ?, ?, ?, ?, ?)";
                $inv_stmt = $conn->prepare($inv_query);
                $inv_stmt->execute([$invoice_number, $export_id, $customer_id, $export_date, $subtotal, $tax, $shipping_cost, $total_amount]);
                
                $invoice_id = $conn->lastInsertId();
                $item_query = "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price, total) VALUES (?, ?, ?, ?, ?)";
                $item_stmt = $conn->prepare($item_query);
                $item_stmt->execute([$invoice_id, $product_id, $quantity, $unit_price, $subtotal]);
                
                $conn->commit();
                
                setFlashMessage('success', 'Export created successfully, inventory deducted, and invoice generated.');
                redirect('/jupiter-import-export/admin/exports/view.php?id=' . $export_id);
            } catch (Exception $e) {
                $conn->rollBack();
                $error = 'Failed to create export. Error: ' . $e->getMessage();
            }
        }
    }
}

include '../../includes/header.php';
?>
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">New Export</h2>
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
                    <label class="form-label">Export Number <span class="text-danger">*</span></label>
                    <input type="text" name="export_number" class="form-control" required value="EXP-<?php echo time(); ?>">
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Export Date <span class="text-danger">*</span></label>
                    <input type="date" name="export_date" class="form-control" required value="<?php echo date('Y-m-d'); ?>">
                </div>
                
                <div class="col-md-6 mb-3">
                    <label class="form-label">Customer <span class="text-danger">*</span></label>
                    <select name="customer_id" class="form-select" required>
                        <option value="">Select Customer</option>
                        <?php foreach($customers as $c): ?>
                            <option value="<?php echo $c['id']; ?>"><?php echo htmlspecialchars($c['company_name']); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-6 mb-3">
                    <label class="form-label">Product <span class="text-danger">*</span></label>
                    <select name="product_id" id="product_id" class="form-select" required onchange="updatePriceAndStock()">
                        <option value="" data-price="0" data-stock="0">Select Product</option>
                        <?php foreach($products as $p): ?>
                            <option value="<?php echo $p['id']; ?>" data-price="<?php echo $p['price']; ?>" data-stock="<?php echo $p['available_quantity']; ?>">
                                <?php echo htmlspecialchars($p['product_name']); ?> (Stock: <?php echo $p['available_quantity']; ?>)
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <div class="col-md-3 mb-3">
                    <label class="form-label">Quantity <span class="text-danger">*</span></label>
                    <input type="number" name="quantity" class="form-control" required min="1">
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Unit Price ($) <span class="text-danger">*</span></label>
                    <input type="number" name="unit_price" id="unit_price" step="0.01" class="form-control" required>
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Shipping Cost ($)</label>
                    <input type="number" name="shipping_cost" step="0.01" class="form-control" value="0">
                </div>
                <div class="col-md-3 mb-3">
                    <label class="form-label">Tax ($)</label>
                    <input type="number" name="tax" step="0.01" class="form-control" value="0">
                </div>
                
                <div class="col-md-12 mb-3">
                    <label class="form-label">Remarks</label>
                    <textarea name="remarks" class="form-control" rows="2"></textarea>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Create Export</button>
        </form>
    </div>
</div>

<script>
function updatePriceAndStock() {
    var select = document.getElementById('product_id');
    var selected = select.options[select.selectedIndex];
    var price = selected.getAttribute('data-price');
    if(price) {
        document.getElementById('unit_price').value = price;
    }
}
</script>
<?php include '../../includes/footer.php'; ?>
"""

exports_view = """<?php
require_once '../../config/database.php';
require_once '../../includes/auth.php';

if (!isset($_GET['id'])) {
    redirect('/jupiter-import-export/admin/exports/index.php');
}

$id = (int)$_GET['id'];
$error = '';

$stmt = $conn->prepare("
    SELECT e.*, p.product_name, p.product_code, c.company_name, u.name as created_by_name 
    FROM exports e 
    JOIN products p ON e.product_id = p.id 
    JOIN customers c ON e.customer_id = c.id 
    JOIN users u ON e.created_by = u.id 
    WHERE e.id = ?
");
$stmt->execute([$id]);
$export = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$export) {
    redirect('/jupiter-import-export/admin/exports/index.php');
}

// Fetch invoice if exists
$inv_stmt = $conn->prepare("SELECT id FROM invoices WHERE export_id = ?");
$inv_stmt->execute([$id]);
$invoice = $inv_stmt->fetch(PDO::FETCH_ASSOC);

if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_POST['update_status'])) {
    $new_status = $_POST['status'];
    if ($export['status'] != 'Delivered' && $export['status'] != 'Cancelled') {
        $stmt = $conn->prepare("UPDATE exports SET status = ? WHERE id = ?");
        
        if ($stmt->execute([$new_status, $id])) {
            setFlashMessage('success', 'Export status updated.');
            redirect('/jupiter-import-export/admin/exports/view.php?id=' . $id);
        }
    }
}

include '../../includes/header.php';
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2 class="h4 mb-0">Export Details: <?php echo htmlspecialchars($export['export_number']); ?></h2>
    <div>
        <?php if($invoice): ?>
        <a href="../invoices/view.php?id=<?php echo $invoice['id']; ?>" class="btn btn-info text-white"><i class="bi bi-receipt"></i> View Invoice</a>
        <?php endif; ?>
        <a href="index.php" class="btn btn-outline-secondary"><i class="bi bi-arrow-left"></i> Back</a>
    </div>
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
                    <div class="col-sm-4 text-muted">Customer</div>
                    <div class="col-sm-8 fw-bold"><?php echo htmlspecialchars($export['company_name']); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Date</div>
                    <div class="col-sm-8"><?php echo date('d M Y', strtotime($export['export_date'])); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Product</div>
                    <div class="col-sm-8"><?php echo htmlspecialchars($export['product_code'] . ' - ' . $export['product_name']); ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Quantity</div>
                    <div class="col-sm-8"><?php echo $export['quantity']; ?></div>
                </div>
                <div class="row mb-3">
                    <div class="col-sm-4 text-muted">Remarks</div>
                    <div class="col-sm-8"><?php echo nl2br(htmlspecialchars($export['remarks'])); ?></div>
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
                    <span class="text-muted">Unit Price:</span>
                    <span>$<?php echo number_format($export['unit_price'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Subtotal:</span>
                    <span>$<?php echo number_format($export['quantity'] * $export['unit_price'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Shipping:</span>
                    <span>$<?php echo number_format($export['shipping_cost'], 2); ?></span>
                </div>
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Tax:</span>
                    <span>$<?php echo number_format($export['tax'], 2); ?></span>
                </div>
                <hr>
                <div class="d-flex justify-content-between mb-3 fw-bold">
                    <span>Grand Total:</span>
                    <span class="text-primary">$<?php echo number_format($export['total_amount'], 2); ?></span>
                </div>
                
                <div class="mb-3">
                    <label class="text-muted mb-1 d-block">Current Status:</label>
                    <h5>
                        <?php 
                        $bg = 'secondary';
                        if($export['status'] == 'Delivered') $bg = 'success';
                        elseif($export['status'] == 'Shipped') $bg = 'info';
                        elseif($export['status'] == 'Processing') $bg = 'primary';
                        elseif($export['status'] == 'Cancelled') $bg = 'danger';
                        ?>
                        <span class="badge bg-<?php echo $bg; ?>"><?php echo $export['status']; ?></span>
                    </h5>
                </div>
                
                <?php if ($export['status'] != 'Delivered' && $export['status'] != 'Cancelled'): ?>
                <form method="POST" action="">
                    <input type="hidden" name="update_status" value="1">
                    <div class="mb-3">
                        <select name="status" class="form-select">
                            <option value="Processing" <?php echo $export['status'] == 'Processing' ? 'selected' : ''; ?>>Processing</option>
                            <option value="Shipped" <?php echo $export['status'] == 'Shipped' ? 'selected' : ''; ?>>Shipped</option>
                            <option value="Delivered" <?php echo $export['status'] == 'Delivered' ? 'selected' : ''; ?>>Delivered</option>
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

with open(os.path.join(exports_dir, 'index.php'), 'w', encoding='utf-8') as f:
    f.write(exports_index)
with open(os.path.join(exports_dir, 'add.php'), 'w', encoding='utf-8') as f:
    f.write(exports_add)
with open(os.path.join(exports_dir, 'view.php'), 'w', encoding='utf-8') as f:
    f.write(exports_view)

print("Exports module generated.")
