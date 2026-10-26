CREATE TABLE spec (
  spec_id INT AUTO_INCREMENT PRIMARY KEY,
  spec_name VARCHAR(60) NOT NULL COMMENT 'Medical specialty'
) COMMENT='Specialties';
INSERT INTO spec (spec_name) VALUES ('Cardiology'),('Pediatrics'),('Dermatology'),('Neurology'),('General Medicine'),('Orthopedics');
CREATE TABLE doc (
  doc_id INT AUTO_INCREMENT PRIMARY KEY,
  doc_name VARCHAR(100) NOT NULL COMMENT 'Doctor full name',
  spec_id INT NOT NULL,
  hire_dt DATE,
  FOREIGN KEY (spec_id) REFERENCES spec(spec_id)
) COMMENT='Doctors';
CREATE TABLE pat (
  pat_id INT AUTO_INCREMENT PRIMARY KEY,
  pat_name VARCHAR(100) NOT NULL COMMENT 'Patient full name',
  birth_dt DATE COMMENT 'Date of birth',
  gender ENUM('M','F') NOT NULL,
  city VARCHAR(60)
) COMMENT='Patients';
CREATE TABLE appt (
  appt_id INT AUTO_INCREMENT PRIMARY KEY,
  pat_id INT NOT NULL,
  doc_id INT NOT NULL,
  appt_dt DATETIME NOT NULL COMMENT 'Appointment date and time',
  status ENUM('scheduled','completed','no_show','cancelled') NOT NULL,
  fee DECIMAL(8,2) COMMENT 'Amount charged',
  FOREIGN KEY (pat_id) REFERENCES pat(pat_id),
  FOREIGN KEY (doc_id) REFERENCES doc(doc_id)
) COMMENT='Appointments';
CREATE TABLE med (
  med_id INT AUTO_INCREMENT PRIMARY KEY,
  med_name VARCHAR(80) NOT NULL,
  unit_price DECIMAL(8,2)
) COMMENT='Medications';
INSERT INTO med (med_name, unit_price) VALUES ('Ibuprofen',12.50),('Amoxicillin',45.00),('Loratadine',20.00),('Omeprazole',30.00),('Paracetamol',8.00),('Metformin',55.00);
CREATE TABLE presc (
  presc_id INT AUTO_INCREMENT PRIMARY KEY,
  appt_id INT NOT NULL,
  med_id INT NOT NULL,
  qty INT NOT NULL COMMENT 'Units prescribed',
  FOREIGN KEY (appt_id) REFERENCES appt(appt_id),
  FOREIGN KEY (med_id) REFERENCES med(med_id)
) COMMENT='Prescriptions issued in an appointment';
