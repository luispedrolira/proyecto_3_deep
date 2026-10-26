CREATE TABLE clientes_t (
  cte_id INT AUTO_INCREMENT PRIMARY KEY,
  cte_nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del cliente',
  telefono VARCHAR(15)
) COMMENT='Clientes del taller';
CREATE TABLE vehiculos (
  veh_id INT AUTO_INCREMENT PRIMARY KEY,
  placa VARCHAR(10) NOT NULL UNIQUE,
  marca ENUM('Toyota','Honda','Nissan','Mazda','Hyundai','Kia') NOT NULL,
  anio INT NOT NULL COMMENT 'Año del modelo',
  cte_id INT NOT NULL,
  FOREIGN KEY (cte_id) REFERENCES clientes_t(cte_id)
) COMMENT='Vehículos de los clientes';
CREATE TABLE mecanicos (
  mec_id INT AUTO_INCREMENT PRIMARY KEY,
  mec_nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del mecánico',
  nivel ENUM('junior','senior','maestro') NOT NULL
) COMMENT='Mecánicos';
CREATE TABLE servicios (
  srv_id INT AUTO_INCREMENT PRIMARY KEY,
  srv_nombre VARCHAR(60) NOT NULL,
  costo_base DECIMAL(8,2) NOT NULL
) COMMENT='Catálogo de servicios';
INSERT INTO servicios (srv_nombre, costo_base) VALUES ('Cambio de aceite',350),('Alineación',250),('Frenos',800),('Afinamiento',1200),('Diagnóstico',200),('Suspensión',1500);
CREATE TABLE ordenes_trabajo (
  ot_id INT AUTO_INCREMENT PRIMARY KEY,
  veh_id INT NOT NULL,
  mec_id INT NOT NULL,
  srv_id INT NOT NULL,
  fec_ingreso DATE NOT NULL,
  fec_entrega DATE COMMENT 'NULL si el vehículo no se ha entregado',
  total DECIMAL(10,2) NOT NULL COMMENT 'Total cobrado',
  FOREIGN KEY (veh_id) REFERENCES vehiculos(veh_id),
  FOREIGN KEY (mec_id) REFERENCES mecanicos(mec_id),
  FOREIGN KEY (srv_id) REFERENCES servicios(srv_id)
) COMMENT='Órdenes de trabajo';
