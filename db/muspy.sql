PRAGMA user_version=1;
PRAGMA journal_mode=WAL;

CREATE TABLE "app_artist" (
    "id" integer NOT NULL PRIMARY KEY,
    "mbid" varchar(36) NOT NULL UNIQUE,
    "name" varchar(512) NOT NULL,
    "sort_name" varchar(512) NOT NULL,
    "country" varchar(2) NOT NULL,
    "disambiguation" varchar(512) NOT NULL
);
CREATE TABLE "app_releasegroup" (
    "id" integer NOT NULL PRIMARY KEY,
    "artist_id" integer NOT NULL REFERENCES "app_artist" ("id"),
    "mbid" varchar(36) NOT NULL UNIQUE,
    "name" varchar(512) NOT NULL,
    "type" varchar(16) NOT NULL,
    "date" integer NOT NULL,
    "is_deleted" bool NOT NULL
);
CREATE TABLE "app_userartist" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id"),
    "artist_id" integer NOT NULL REFERENCES "app_artist" ("id"),
    UNIQUE ("user_id", "artist_id")
);
CREATE TABLE "app_userprofile" (
    "id" integer NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id"),
    "notify" bool NOT NULL,
    "notify_album" bool NOT NULL,
    "notify_single" bool NOT NULL,
    "notify_ep" bool NOT NULL,
    "notify_live" bool NOT NULL,
    "notify_compilation" bool NOT NULL,
    "notify_remix" bool NOT NULL,
    "notify_other" bool NOT NULL,
    "email_activated" bool NOT NULL,
    "activation_code" varchar(16) NOT NULL,
    "reset_code" varchar(16) NOT NULL
);
CREATE TABLE "auth_user" (
    "id" integer NOT NULL PRIMARY KEY,
    "username" varchar(30) NOT NULL UNIQUE,
    "first_name" varchar(30) NOT NULL,
    "last_name" varchar(30) NOT NULL,
    "email" varchar(75) NOT NULL UNIQUE,
    "password" varchar(128) NOT NULL,
    "is_staff" bool NOT NULL,
    "is_active" bool NOT NULL,
    "is_superuser" bool NOT NULL,
    "last_login" datetime NOT NULL,
    "date_joined" datetime NOT NULL
);
CREATE TABLE "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" datetime NOT NULL
);
CREATE INDEX "app_artist_sort_name" ON "app_artist" ("sort_name");
CREATE INDEX "app_releasegroup_artist_id" ON "app_releasegroup" ("artist_id");
CREATE INDEX "app_userartist_artist_id" ON "app_userartist" ("artist_id");
CREATE INDEX "app_userartist_user_id" ON "app_userartist" ("user_id");
CREATE INDEX "django_session_expire_date" ON "django_session" ("expire_date");
