CREATE TABLE suc (
  suc_id INT AUTO_INCREMENT PRIMARY KEY,
  suc_nom VARCHAR(60) NOT NULL COMMENT 'Nombre de la sucursal',
  ciudad VARCHAR(60) NOT NULL
) COMMENT='Sucursales del banco';
INSERT INTO suc (suc_nom, ciudad) VALUES ('Central','Guatemala'),('Zona 10','Guatemala'),('Xela Centro','Quetzaltenango'),('Antigua Plaza','Antigua'),('Cobán Norte','Cobán');
CREATE TABLE cli (
  cli_id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL COMMENT 'Nombre del cliente',
  dpi VARCHAR(20) UNIQUE COMMENT 'Documento de identificación',
  fec_nac DATE COMMENT 'Fecha de nacimiento',
  suc_id INT NOT NULL COMMENT 'Sucursal donde se afilió',
  FOREIGN KEY (suc_id) REFERENCES suc(suc_id)
) COMMENT='Clientes';
CREATE TABLE cta (
  cta_id INT AUTO_INCREMENT PRIMARY KEY,
  cli_id INT NOT NULL,
  tipo ENUM('ahorro','monetaria','plazo_fijo') NOT NULL COMMENT 'Tipo de cuenta',
  saldo DECIMAL(12,2) NOT NULL COMMENT 'Saldo actual en quetzales',
  fec_apertura DATE NOT NULL,
  FOREIGN KEY (cli_id) REFERENCES cli(cli_id)
) COMMENT='Cuentas bancarias';
CREATE TABLE mov (
  mov_id INT AUTO_INCREMENT PRIMARY KEY,
  cta_id INT NOT NULL,
  fec DATETIME NOT NULL COMMENT 'Fecha y hora del movimiento',
  tipo ENUM('deposito','retiro','transferencia') NOT NULL,
  monto DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (cta_id) REFERENCES cta(cta_id)
) COMMENT='Movimientos de las cuentas';
CREATE TABLE prest (
  prest_id INT AUTO_INCREMENT PRIMARY KEY,
  cli_id INT NOT NULL,
  monto DECIMAL(12,2) NOT NULL COMMENT 'Monto otorgado',
  tasa DECIMAL(5,4) NOT NULL COMMENT 'Tasa de interés anual',
  fec_otorg DATE NOT NULL COMMENT 'Fecha de otorgamiento',
  estado ENUM('vigente','pagado','moroso') NOT NULL,
  FOREIGN KEY (cli_id) REFERENCES cli(cli_id)
) COMMENT='Préstamos';
