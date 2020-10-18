CREATE TABLE IF NOT EXISTS scores (
	player_name TEXT PRIMARY KEY,
	pdf_readers TEXT NOT NULL,   /* comma-separated list of strings */
	secrets_found TEXT NOT NULL, /* comma-separated list of strings */
	version TEXT NOT NULL,       /* game version for latest score submitted */
	submission_date timestamp    /* date for latest score submitted */
);
