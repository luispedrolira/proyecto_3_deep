CREATE TABLE departments (
  dept_id INT AUTO_INCREMENT PRIMARY KEY,
  dept_name VARCHAR(60) NOT NULL,
  location VARCHAR(60) COMMENT 'City where the department is located'
) COMMENT='Company departments';
INSERT INTO departments (dept_name, location) VALUES ('Sales','Guatemala'),('Engineering','Antigua'),('Finance','Guatemala'),('Marketing','Quetzaltenango'),('Support','Cobán'),('Legal','Guatemala');
CREATE TABLE jobs (
  job_id INT AUTO_INCREMENT PRIMARY KEY,
  job_title VARCHAR(60) NOT NULL,
  min_salary DECIMAL(10,2),
  max_salary DECIMAL(10,2)
) COMMENT='Job positions';
INSERT INTO jobs (job_title, min_salary, max_salary) VALUES ('Analyst',6000,12000),('Developer',9000,20000),('Manager',15000,30000),('Assistant',4000,7000),('Accountant',7000,14000);
CREATE TABLE employees (
  emp_id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(40) NOT NULL,
  last_name VARCHAR(40) NOT NULL,
  hire_date DATE NOT NULL,
  salary DECIMAL(10,2) NOT NULL COMMENT 'Current monthly salary',
  dept_id INT,
  job_id INT,
  manager_id INT COMMENT 'emp_id of the direct manager',
  FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
  FOREIGN KEY (job_id) REFERENCES jobs(job_id)
) COMMENT='Employees';
CREATE TABLE projects (
  proj_id INT AUTO_INCREMENT PRIMARY KEY,
  proj_name VARCHAR(80) NOT NULL,
  budget DECIMAL(12,2),
  start_date DATE,
  status ENUM('active','completed','cancelled') NOT NULL
) COMMENT='Projects';
CREATE TABLE emp_projects (
  emp_id INT NOT NULL,
  proj_id INT NOT NULL,
  hours_worked INT COMMENT 'Total hours the employee worked on the project',
  PRIMARY KEY (emp_id, proj_id),
  FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
  FOREIGN KEY (proj_id) REFERENCES projects(proj_id)
) COMMENT='Assignment of employees to projects';
