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
	"created"	NUMERIC NOT NULL DEFAULT CURRENT_TIMESTAMP,
	"transdate"	TEXT NOT NULL,
	"desc"	TEXT NOT NULL,
	"amount"	NUMERIC NOT NULL,
	"category"	TEXT NOT NULL,
	"sourceAcc"	TEXT NOT NULL,
	"destinationAcc"	TEXT NOT NULL,
	"score"	NUMERIC NOT NULL DEFAULT 0,
	"session_key"	Text NOT NULL DEFAULT '',
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("created") REFERENCES ""
)

CREATE TABLE "_sourceAccount" ("id"	INTEGER NOT NULL UNIQUE,"desc" TEXT NOT NULL,PRIMARY KEY("id" AUTOINCREMENT))

CREATE TABLE "_sourceAccountCsvMapping" (
	"id"	INTEGER UNIQUE,
	"_sourceAccount_id"	INTEGER,
	"from_csv_fld"	TEXT NOT NULL,
	"to_sqldesc_fld"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("_sourceAccount_id") REFERENCES "_sourceAccount"("id") ON DELETE CASCADE
)

CREATE TABLE "accounts" (
	"id"	INTEGER NOT NULL,
	"account_name"	TEXT DEFAULT ' ',
	"has_header"	INTEGER DEFAULT 0,
	PRIMARY KEY("id")
)

CREATE TABLE "account_columns_map" (
	"id"	INTEGER NOT NULL,
	"account_id"	INTEGER NOT NULL,
	"src_column_name"	TEXT NOT NULL DEFAULT ' ',
	"des_column_name"	TEXT NOT NULL DEFAULT ' ',
	"is_drop"	INTEGER DEFAULT 0,
	"format"	TEXT DEFAULT ' ',
	"custom"	INTEGER DEFAULT 0,
	"custom_formula"	TEXT DEFAULT ' ',
	PRIMARY KEY("id"),
	FOREIGN KEY("account_id") REFERENCES "accounts"("id") ON DELETE CASCADE
)
