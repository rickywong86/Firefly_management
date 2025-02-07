DROP TABLE IF EXISTS __category;
DROP TABLE IF EXISTS __transaction;

CREATE TABLE __category (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE NOT NULL,
  category TEXT NOT NULL,
  destinationAcc TEXT NOT NULL
);

CREATE TABLE __transaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  transdate datetime NOT NULL,
  desc TEXT NOT NULL,
  amount Decimal(5, 2) NOT NULL,
  category TEXT NOT NULL,
  sourceAcc TEXT NOT NULL,
  destinationAcc TEXT NOT NULL,
  filename TEXT NOT NULL,
  similarityScore Decimal(3, 2) NOT NULL
);