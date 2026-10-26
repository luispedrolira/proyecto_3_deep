CREATE TABLE planes (
  id_plan INT AUTO_INCREMENT PRIMARY KEY,
  nombre_plan VARCHAR(40) NOT NULL,
  precio_mensual DECIMAL(8,2) NOT NULL
) COMMENT='Planes de membresía';
INSERT INTO planes (nombre_plan, precio_mensual) VALUES ('Básico',150),('Plus',250),('Premium',400),('Estudiante',120);
CREATE TABLE miembros (
  id_miembro INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del miembro',
  fecha_inscripcion DATE NOT NULL,
  id_plan INT NOT NULL,
  activo TINYINT(1) NOT NULL COMMENT '1 si la membresía está activa',
  FOREIGN KEY (id_plan) REFERENCES planes(id_plan)
) COMMENT='Miembros del gimnasio';
CREATE TABLE instructores (
  id_instructor INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL COMMENT 'Nombre del instructor',
  especialidad ENUM('yoga','spinning','crossfit','pesas','natación') NOT NULL
) COMMENT='Instructores';
CREATE TABLE clases (
  id_clase INT AUTO_INCREMENT PRIMARY KEY,
  nombre_clase VARCHAR(60) NOT NULL,
  id_instructor INT NOT NULL,
  dia_semana ENUM('lunes','martes','miércoles','jueves','viernes','sábado') NOT NULL,
  cupo INT NOT NULL COMMENT 'Capacidad máxima',
  FOREIGN KEY (id_instructor) REFERENCES instructores(id_instructor)
) COMMENT='Clases grupales';
CREATE TABLE asistencias (
  id_asistencia INT AUTO_INCREMENT PRIMARY KEY,
  id_miembro INT NOT NULL,
  id_clase INT NOT NULL,
  fecha DATE NOT NULL,
  FOREIGN KEY (id_miembro) REFERENCES miembros(id_miembro),
  FOREIGN KEY (id_clase) REFERENCES clases(id_clase)
) COMMENT='Asistencia de miembros a clases';
CREATE TABLE pagos (
  id_pago INT AUTO_INCREMENT PRIMARY KEY,
  id_miembro INT NOT NULL,
  fecha_pago DATE NOT NULL,
  monto DECIMAL(8,2) NOT NULL,
  metodo ENUM('efectivo','tarjeta','transferencia') NOT NULL,
  FOREIGN KEY (id_miembro) REFERENCES miembros(id_miembro)
) COMMENT='Pagos de mensualidades';
