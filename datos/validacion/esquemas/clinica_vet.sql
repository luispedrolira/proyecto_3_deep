CREATE TABLE especies (
  id_especie INT AUTO_INCREMENT PRIMARY KEY,
  especie VARCHAR(40) NOT NULL COMMENT 'Nombre de la especie'
) COMMENT='Especies atendidas';
INSERT INTO especies (especie) VALUES ('Perro'),('Gato'),('Conejo'),('Ave'),('Hámster');
CREATE TABLE duenos (
  id_dueno INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre completo del dueño',
  telefono VARCHAR(15),
  ciudad VARCHAR(60) COMMENT 'Ciudad de residencia'
) COMMENT='Dueños de mascotas';
CREATE TABLE mascotas (
  id_mascota INT AUTO_INCREMENT PRIMARY KEY,
  nombre_mascota VARCHAR(60) NOT NULL,
  id_especie INT NOT NULL,
  id_dueno INT NOT NULL,
  fecha_nacimiento DATE,
  peso_kg DECIMAL(5,2) COMMENT 'Peso en kilogramos',
  FOREIGN KEY (id_especie) REFERENCES especies(id_especie),
  FOREIGN KEY (id_dueno) REFERENCES duenos(id_dueno)
) COMMENT='Mascotas registradas';
CREATE TABLE veterinarios (
  id_vet INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del veterinario',
  especialidad ENUM('general','cirugía','dermatología','exóticos') NOT NULL,
  fecha_contratacion DATE
) COMMENT='Veterinarios de la clínica';
CREATE TABLE consultas (
  id_consulta INT AUTO_INCREMENT PRIMARY KEY,
  id_mascota INT NOT NULL,
  id_vet INT NOT NULL,
  fecha_consulta DATETIME NOT NULL,
  motivo ENUM('vacunación','control','emergencia','cirugía','desparasitación') NOT NULL,
  costo DECIMAL(8,2) NOT NULL COMMENT 'Costo de la consulta en quetzales',
  FOREIGN KEY (id_mascota) REFERENCES mascotas(id_mascota),
  FOREIGN KEY (id_vet) REFERENCES veterinarios(id_vet)
) COMMENT='Consultas veterinarias';
CREATE TABLE tratamientos (
  id_tratamiento INT AUTO_INCREMENT PRIMARY KEY,
  id_consulta INT NOT NULL,
  medicamento VARCHAR(60) NOT NULL,
  dosis_mg INT COMMENT 'Dosis en miligramos',
  dias INT NOT NULL COMMENT 'Duración del tratamiento en días',
  FOREIGN KEY (id_consulta) REFERENCES consultas(id_consulta)
) COMMENT='Tratamientos recetados en cada consulta';
CREATE TABLE facturas (
  id_factura INT AUTO_INCREMENT PRIMARY KEY,
  id_consulta INT NOT NULL,
  fecha_emision DATE NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  pagada TINYINT(1) NOT NULL COMMENT '1 si la factura ya se pagó',
  FOREIGN KEY (id_consulta) REFERENCES consultas(id_consulta)
) COMMENT='Facturas emitidas';
