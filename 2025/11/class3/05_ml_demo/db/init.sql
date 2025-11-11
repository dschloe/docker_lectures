CREATE TABLE IF NOT EXISTS tips (
  id          INT PRIMARY KEY AUTO_INCREMENT,
  total_bill  DECIMAL(10,2),
  tip         DECIMAL(10,2),
  sex         VARCHAR(10),
  smoker      VARCHAR(10),
  day         VARCHAR(10),
  time        VARCHAR(10),     -- 종속변수 (Lunch/Dinner)
  size        INT,
  source      ENUM('initial','manual') DEFAULT 'manual',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tips_audit (
  id          INT PRIMARY KEY AUTO_INCREMENT,
  tips_id     INT,
  action      ENUM('insert') NOT NULL DEFAULT 'insert',
  source      ENUM('initial','manual') NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);