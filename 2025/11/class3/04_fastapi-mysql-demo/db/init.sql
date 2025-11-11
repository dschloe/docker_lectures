CREATE TABLE IF NOT EXISTS demo (
  id  INT PRIMARY KEY AUTO_INCREMENT,
  msg VARCHAR(100)
);
INSERT INTO demo (msg) VALUES
('hello from init.sql'),
('docker + mysql + fastapi (compose)');