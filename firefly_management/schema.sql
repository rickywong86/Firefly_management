DROP TABLE IF EXISTS __category;
DROP TABLE IF EXISTS __transaction;
DROP TABLE IF EXISTS __uploadheader;

CREATE TABLE "__uploadheader" (
	"id"	INTEGER NOT NULL UNIQUE,
	"createddate"	TEXT DEFAULT CURRENT_TIMESTAMP,
	"filename"	TEXT NOT NULL,
	"session_key" TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "__category" (
	"id"	INTEGER NOT NULL UNIQUE,
	"key"	TEXT NOT NULL UNIQUE,
	"category"	TEXT NOT NULL,
	"destinationAcc"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE "__transactions" (
	"id"	INTEGER NOT NULL UNIQUE,
	"__uploadheader_id"	INTEGER,
	"created"	NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"transdate"	TEXT NOT NULL,
	"desc"	TEXT NOT NULL,
	"amount"	NUMERIC NOT NULL,
	"category"	TEXT NOT NULL,
	"sourceAcc"	TEXT NOT NULL,
	"destinationAcc"	TEXT NOT NULL,
	"score"	NUMERIC NOT NULL DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("__uploadheader_id") REFERENCES "__uploadheader"("id") ON DELETE CASCADE
);