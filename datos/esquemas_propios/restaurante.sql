CREATE TABLE cat_menu (
  id_cat INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(40) NOT NULL
) COMMENT='Categorías del menú';
INSERT INTO cat_menu (nombre) VALUES ('Entradas'),('Platos fuertes'),('Postres'),('Bebidas'),('Sopas');
CREATE TABLE platillos (
  id_platillo INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  id_cat INT NOT NULL,
  precio DECIMAL(8,2) NOT NULL,
  disponible TINYINT(1) NOT NULL,
  FOREIGN KEY (id_cat) REFERENCES cat_menu(id_cat)
) COMMENT='Platillos del menú';
CREATE TABLE meseros (
  id_mesero INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del mesero',
  turno ENUM('mañana','tarde','noche') NOT NULL
) COMMENT='Meseros';
CREATE TABLE mesas (
  id_mesa INT AUTO_INCREMENT PRIMARY KEY,
  capacidad INT NOT NULL,
  zona ENUM('interior','terraza','bar') NOT NULL
) COMMENT='Mesas del restaurante';
CREATE TABLE ordenes (
  id_orden INT AUTO_INCREMENT PRIMARY KEY,
  id_mesa INT NOT NULL,
  id_mesero INT NOT NULL,
  fecha_hora DATETIME NOT NULL,
  propina DECIMAL(8,2) COMMENT 'Propina dejada por el cliente',
  FOREIGN KEY (id_mesa) REFERENCES mesas(id_mesa),
  FOREIGN KEY (id_mesero) REFERENCES meseros(id_mesero)
) COMMENT='Órdenes';
CREATE TABLE orden_items (
  id_item INT AUTO_INCREMENT PRIMARY KEY,
  id_orden INT NOT NULL,
  id_platillo INT NOT NULL,
  cantidad INT NOT NULL,
  FOREIGN KEY (id_orden) REFERENCES ordenes(id_orden),
  FOREIGN KEY (id_platillo) REFERENCES platillos(id_platillo)
) COMMENT='Platillos de cada orden';
