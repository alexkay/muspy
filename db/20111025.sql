BEGIN TRANSACTION;

CREATE TABLE "app_releasegroup_tmp" (
    "id" integer NOT NULL PRIMARY KEY,
    "artist_id" integer NOT NULL REFERENCES "app_artist" ("id"),
    "mbid" varchar(36) NOT NULL,
    "name" varchar(512) NOT NULL,
    "type" varchar(16) NOT NULL,
    "date" integer NOT NULL,
    "is_deleted" bool NOT NULL,
    UNIQUE ("artist_id", "mbid")
);

INSERT INTO "app_releasegroup_tmp"
SELECT * FROM "app_releasegroup";

DROP TABLE "app_releasegroup";

ALTER TABLE "app_releasegroup_tmp"
RENAME TO "app_releasegroup";

CREATE INDEX "app_releasegroup_artist_id" ON "app_releasegroup" ("artist_id");
CREATE INDEX "app_releasegroup_mbid" ON "app_releasegroup" ("mbid");
CREATE INDEX "app_releasegroup_date" ON "app_releasegroup" ("date" DESC);

COMMIT;