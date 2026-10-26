CREATE TABLE airlines (
  airline_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(60) NOT NULL,
  country VARCHAR(50)
) COMMENT='Airlines';
INSERT INTO airlines (name, country) VALUES ('Avianca','Colombia'),('Copa','Panamá'),('Aeroméxico','México'),('United','Estados Unidos'),('Iberia','España'),('TAG','Guatemala');
CREATE TABLE airports (
  code CHAR(3) PRIMARY KEY COMMENT 'IATA code',
  name VARCHAR(80) NOT NULL,
  city VARCHAR(60) NOT NULL,
  country VARCHAR(50) NOT NULL
) COMMENT='Airports';
INSERT INTO airports VALUES ('GUA','La Aurora','Guatemala','Guatemala'),('MEX','Benito Juárez','Ciudad de México','México'),('PTY','Tocumen','Panamá','Panamá'),('BOG','El Dorado','Bogotá','Colombia'),('MIA','Miami Intl','Miami','Estados Unidos'),('MAD','Barajas','Madrid','España'),('FRS','Mundo Maya','Flores','Guatemala'),('SAL','Monseñor Romero','San Salvador','El Salvador');
CREATE TABLE flights (
  flight_id INT AUTO_INCREMENT PRIMARY KEY,
  airline_id INT NOT NULL,
  origin CHAR(3) NOT NULL COMMENT 'Origin airport code',
  dest CHAR(3) NOT NULL COMMENT 'Destination airport code',
  dep_time DATETIME NOT NULL COMMENT 'Scheduled departure',
  duration_min INT NOT NULL COMMENT 'Duration in minutes',
  seats INT NOT NULL,
  FOREIGN KEY (airline_id) REFERENCES airlines(airline_id),
  FOREIGN KEY (origin) REFERENCES airports(code),
  FOREIGN KEY (dest) REFERENCES airports(code)
) COMMENT='Scheduled flights';
CREATE TABLE passengers (
  pax_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(100) NOT NULL,
  nationality VARCHAR(50),
  birth_date DATE
) COMMENT='Passengers';
CREATE TABLE bookings (
  booking_id INT AUTO_INCREMENT PRIMARY KEY,
  flight_id INT NOT NULL,
  pax_id INT NOT NULL,
  booking_date DATE NOT NULL,
  class ENUM('economy','business','first') NOT NULL,
  price DECIMAL(10,2) NOT NULL COMMENT 'Ticket price in USD',
  FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
  FOREIGN KEY (pax_id) REFERENCES passengers(pax_id)
) COMMENT='Ticket bookings';
