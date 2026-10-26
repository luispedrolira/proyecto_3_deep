CREATE TABLE categorias (
  id_categoria INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(60) NOT NULL COMMENT 'Nombre de la categoría'
) COMMENT='Categorías de productos';
INSERT INTO categorias (nombre) VALUES ('Electrónica'),('Hogar'),('Deportes'),('Libros'),('Juguetes'),('Ropa');
CREATE TABLE clientes (
  id_cliente INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre completo del cliente',
  email VARCHAR(120) UNIQUE,
  ciudad VARCHAR(60) COMMENT 'Ciudad de residencia',
  fecha_registro DATE COMMENT 'Fecha en que se registró en la tienda'
) COMMENT='Clientes registrados';
CREATE TABLE productos (
  id_producto INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  id_categoria INT NOT NULL,
  precio DECIMAL(10,2) NOT NULL COMMENT 'Precio unitario en quetzales',
  stock INT NOT NULL COMMENT 'Unidades disponibles',
  FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
) COMMENT='Catálogo de productos';
CREATE TABLE pedidos (
  id_pedido INT AUTO_INCREMENT PRIMARY KEY,
  id_cliente INT NOT NULL,
  fecha_pedido DATE NOT NULL,
  estado ENUM('pendiente','enviado','entregado','cancelado') NOT NULL COMMENT 'Estado actual del pedido',
  FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
) COMMENT='Pedidos realizados por los clientes';
CREATE TABLE detalle_pedido (
  id_detalle INT AUTO_INCREMENT PRIMARY KEY,
  id_pedido INT NOT NULL,
  id_producto INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL COMMENT 'Precio cobrado al momento de la compra',
  FOREIGN KEY (id_pedido) REFERENCES pedidos(id_pedido),
  FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
) COMMENT='Líneas de cada pedido';
CREATE TABLE resenas (
  id_resena INT AUTO_INCREMENT PRIMARY KEY,
  id_producto INT NOT NULL,
  id_cliente INT NOT NULL,
  calificacion TINYINT NOT NULL COMMENT 'De 1 a 5 estrellas',
  fecha DATE NOT NULL,
  FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
  FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente)
) COMMENT='Reseñas de productos';
