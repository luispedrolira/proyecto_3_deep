CREATE TABLE fac (
  fac_id INT AUTO_INCREMENT PRIMARY KEY,
  fac_nom VARCHAR(80) NOT NULL COMMENT 'Nombre de la facultad'
) COMMENT='Facultades';
INSERT INTO fac (fac_nom) VALUES ('Ingeniería'),('Ciencias Sociales'),('Medicina'),('Arquitectura'),('Economía');
CREATE TABLE carr (
  carr_id INT AUTO_INCREMENT PRIMARY KEY,
  carr_nom VARCHAR(80) NOT NULL COMMENT 'Nombre de la carrera',
  fac_id INT NOT NULL,
  FOREIGN KEY (fac_id) REFERENCES fac(fac_id)
) COMMENT='Carreras';
INSERT INTO carr (carr_nom, fac_id) VALUES ('Computación',1),('Civil',1),('Psicología',2),('Derecho',2),('Medicina General',3),('Diseño',4),('Administración',5),('Contaduría',5);
CREATE TABLE est (
  est_id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL COMMENT 'Nombre del estudiante',
  carr_id INT NOT NULL COMMENT 'Carrera del estudiante',
  fec_ing DATE COMMENT 'Fecha de ingreso',
  ciudad VARCHAR(60),
  FOREIGN KEY (carr_id) REFERENCES carr(carr_id)
) COMMENT='Estudiantes';
CREATE TABLE prof (
  prof_id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL COMMENT 'Nombre del profesor',
  fac_id INT NOT NULL,
  salario DECIMAL(10,2),
  FOREIGN KEY (fac_id) REFERENCES fac(fac_id)
) COMMENT='Profesores';
CREATE TABLE cur (
  cur_id INT AUTO_INCREMENT PRIMARY KEY,
  cur_nom VARCHAR(80) NOT NULL COMMENT 'Nombre del curso',
  creditos INT NOT NULL,
  prof_id INT,
  FOREIGN KEY (prof_id) REFERENCES prof(prof_id)
) COMMENT='Cursos';
CREATE TABLE insc (
  insc_id INT AUTO_INCREMENT PRIMARY KEY,
  est_id INT NOT NULL,
  cur_id INT NOT NULL,
  ciclo VARCHAR(10) COMMENT 'Ciclo académico, p. ej. 2024-1',
  nota DECIMAL(5,2) COMMENT 'Nota final de 0 a 100',
  fec_insc DATE COMMENT 'Fecha de inscripción',
  FOREIGN KEY (est_id) REFERENCES est(est_id),
  FOREIGN KEY (cur_id) REFERENCES cur(cur_id)
) COMMENT='Inscripciones de estudiantes en cursos';
