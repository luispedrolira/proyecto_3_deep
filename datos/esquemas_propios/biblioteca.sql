CREATE TABLE generos (
  id_genero INT AUTO_INCREMENT PRIMARY KEY,
  genero VARCHAR(50) NOT NULL
) COMMENT='Géneros literarios';
INSERT INTO generos (genero) VALUES ('Novela'),('Ciencia ficción'),('Historia'),('Poesía'),('Infantil'),('Ensayo');
CREATE TABLE autores (
  id_autor INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del autor',
  pais VARCHAR(50) COMMENT 'País de origen'
) COMMENT='Autores';
CREATE TABLE libros (
  id_libro INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(150) NOT NULL,
  id_autor INT NOT NULL,
  id_genero INT NOT NULL,
  anio_publicacion INT,
  ejemplares INT NOT NULL COMMENT 'Copias físicas disponibles',
  FOREIGN KEY (id_autor) REFERENCES autores(id_autor),
  FOREIGN KEY (id_genero) REFERENCES generos(id_genero)
) COMMENT='Libros del catálogo';
CREATE TABLE socios (
  id_socio INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del socio',
  fecha_alta DATE COMMENT 'Fecha de afiliación',
  tipo ENUM('estudiante','general','docente') NOT NULL
) COMMENT='Socios de la biblioteca';
CREATE TABLE prestamos (
  id_prestamo INT AUTO_INCREMENT PRIMARY KEY,
  id_libro INT NOT NULL,
  id_socio INT NOT NULL,
  fecha_prestamo DATE NOT NULL,
  fecha_devolucion DATE COMMENT 'NULL si aún no se devuelve',
  FOREIGN KEY (id_libro) REFERENCES libros(id_libro),
  FOREIGN KEY (id_socio) REFERENCES socios(id_socio)
) COMMENT='Préstamos de libros';
CREATE TABLE multas (
  id_multa INT AUTO_INCREMENT PRIMARY KEY,
  id_prestamo INT NOT NULL,
  monto DECIMAL(8,2) NOT NULL,
  pagada TINYINT(1) NOT NULL COMMENT '1 si ya se pagó',
  FOREIGN KEY (id_prestamo) REFERENCES prestamos(id_prestamo)
) COMMENT='Multas por retraso';
