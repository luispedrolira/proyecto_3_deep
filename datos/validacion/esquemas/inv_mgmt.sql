CREATE TABLE cat (
  cat_id INT AUTO_INCREMENT PRIMARY KEY,
  cat_nm VARCHAR(50) NOT NULL COMMENT 'Category name'
) COMMENT='Product categories';
INSERT INTO cat (cat_nm) VALUES ('Tools'),('Electrical'),('Plumbing'),('Paint'),('Garden'),('Hardware');
CREATE TABLE sup (
  sup_id INT AUTO_INCREMENT PRIMARY KEY,
  sup_nm VARCHAR(100) NOT NULL COMMENT 'Supplier name',
  ctry VARCHAR(50) COMMENT 'Supplier country',
  rating DECIMAL(3,2) COMMENT 'Supplier rating from 1 to 5'
) COMMENT='Suppliers';
CREATE TABLE prod (
  prod_id INT AUTO_INCREMENT PRIMARY KEY,
  prod_nm VARCHAR(100) NOT NULL COMMENT 'Product name',
  cat_id INT NOT NULL,
  sup_id INT NOT NULL COMMENT 'Main supplier',
  unit_cost DECIMAL(10,2) NOT NULL COMMENT 'Purchase cost per unit',
  list_price DECIMAL(10,2) NOT NULL COMMENT 'Sale price per unit',
  FOREIGN KEY (cat_id) REFERENCES cat(cat_id),
  FOREIGN KEY (sup_id) REFERENCES sup(sup_id)
) COMMENT='Products';
CREATE TABLE whs (
  whs_id INT AUTO_INCREMENT PRIMARY KEY,
  whs_nm VARCHAR(60) NOT NULL COMMENT 'Warehouse name',
  city VARCHAR(60) NOT NULL,
  cap_units INT NOT NULL COMMENT 'Maximum capacity in units'
) COMMENT='Warehouses';
INSERT INTO whs (whs_nm, city, cap_units) VALUES ('WH-North','Cobán',5000),('WH-Central','Guatemala',12000),('WH-West','Quetzaltenango',6000),('WH-South','Escuintla',8000);
CREATE TABLE stk (
  whs_id INT NOT NULL,
  prod_id INT NOT NULL,
  qty_on_hand INT NOT NULL COMMENT 'Units currently in stock',
  reorder_lvl INT NOT NULL COMMENT 'Reorder when qty_on_hand falls below this level',
  PRIMARY KEY (whs_id, prod_id),
  FOREIGN KEY (whs_id) REFERENCES whs(whs_id),
  FOREIGN KEY (prod_id) REFERENCES prod(prod_id)
) COMMENT='Stock per warehouse and product';
CREATE TABLE po (
  po_id INT AUTO_INCREMENT PRIMARY KEY,
  sup_id INT NOT NULL,
  whs_id INT NOT NULL COMMENT 'Destination warehouse',
  ord_dt DATE NOT NULL COMMENT 'Order date',
  rcv_dt DATE COMMENT 'Reception date, NULL if not received yet',
  sts ENUM('open','received','cancelled') NOT NULL COMMENT 'Purchase order status',
  FOREIGN KEY (sup_id) REFERENCES sup(sup_id),
  FOREIGN KEY (whs_id) REFERENCES whs(whs_id)
) COMMENT='Purchase orders';
CREATE TABLE po_ln (
  po_ln_id INT AUTO_INCREMENT PRIMARY KEY,
  po_id INT NOT NULL,
  prod_id INT NOT NULL,
  qty INT NOT NULL COMMENT 'Units ordered',
  unit_cost DECIMAL(10,2) NOT NULL COMMENT 'Agreed cost per unit',
  FOREIGN KEY (po_id) REFERENCES po(po_id),
  FOREIGN KEY (prod_id) REFERENCES prod(prod_id)
) COMMENT='Purchase order lines';
