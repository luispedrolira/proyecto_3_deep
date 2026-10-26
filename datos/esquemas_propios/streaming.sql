CREATE TABLE plans (
  plan_id INT AUTO_INCREMENT PRIMARY KEY,
  plan_name VARCHAR(30) NOT NULL,
  monthly_fee DECIMAL(6,2) NOT NULL
) COMMENT='Subscription plans';
INSERT INTO plans (plan_name, monthly_fee) VALUES ('Basic',6.99),('Standard',10.99),('Premium',15.99);
CREATE TABLE genres (
  genre_id INT AUTO_INCREMENT PRIMARY KEY,
  genre VARCHAR(40) NOT NULL
) COMMENT='Genres';
INSERT INTO genres (genre) VALUES ('Drama'),('Comedy'),('Action'),('Documentary'),('Horror'),('Animation');
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  country VARCHAR(50),
  signup_date DATE NOT NULL,
  plan_id INT NOT NULL,
  FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
) COMMENT='Platform users';
CREATE TABLE titles (
  title_id INT AUTO_INCREMENT PRIMARY KEY,
  title_name VARCHAR(120) NOT NULL,
  genre_id INT NOT NULL,
  release_year INT,
  type ENUM('movie','series') NOT NULL,
  duration_min INT COMMENT 'Duration in minutes (per episode for series)',
  FOREIGN KEY (genre_id) REFERENCES genres(genre_id)
) COMMENT='Catalog titles';
CREATE TABLE views (
  view_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title_id INT NOT NULL,
  view_date DATE NOT NULL,
  minutes_watched INT NOT NULL,
  rating TINYINT COMMENT 'User rating from 1 to 5, NULL if not rated',
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (title_id) REFERENCES titles(title_id)
) COMMENT='Viewing history';
