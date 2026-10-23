import os

base_dir = r"C:\Users\hp\Desktop\jupitar\jupiter-import-export\admin"
entities = ["products", "suppliers", "customers"]

for entity in entities:
    index_file = os.path.join(base_dir, entity, 'index.php')
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if delete button already exists
    if 'delete.php' not in content:
        # Replace the edit button line with edit + delete
        old_action = """<a href="edit.php?id=<?php echo $item['id']; ?>" class="btn btn-sm btn-outline-primary"><i class="bi bi-pencil"></i> Edit</a>"""
        new_action = """<a href="edit.php?id=<?php echo $item['id']; ?>" class="btn btn-sm btn-outline-primary"><i class="bi bi-pencil"></i> Edit</a>
                                <a href="delete.php?id=<?php echo $item['id']; ?>" class="btn btn-sm btn-outline-danger" onclick="return confirm('Are you sure you want to delete this record?');"><i class="bi bi-trash"></i> Delete</a>"""
        
        content = content.replace(old_action, new_action)
        
        # Add error flash message display
        if "displayFlashMessage('error')" not in content:
            success_block = """<?php if ($msg = displayFlashMessage('success')): ?>
    <div class="alert alert-success"><?php echo $msg; ?></div>
<?php endif; ?>"""
            new_block = success_block + """
<?php if ($msg = displayFlashMessage('error')): ?>
    <div class="alert alert-danger"><?php echo $msg; ?></div>
<?php endif; ?>"""
            content = content.replace(success_block, new_block)
            
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)

print("Index files updated with delete button.")
