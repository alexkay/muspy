CREATE TABLE "piston_nonce" (
    "id" integer NOT NULL PRIMARY KEY,
    "token_key" varchar(18) NOT NULL,
    "consumer_key" varchar(18) NOT NULL,
    "key" varchar(255) NOT NULL
);
CREATE TABLE "piston_resource" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(255) NOT NULL,
    "url" text NOT NULL,
    "is_readonly" bool NOT NULL
);
CREATE TABLE "piston_consumer" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(255) NOT NULL,
    "description" text NOT NULL,
    "key" varchar(18) NOT NULL,
    "secret" varchar(32) NOT NULL,
    "status" varchar(16) NOT NULL,
    "user_id" integer REFERENCES "auth_user" ("id")
);
CREATE TABLE "piston_token" (
    "id" integer NOT NULL PRIMARY KEY,
    "key" varchar(18) NOT NULL,
    "secret" varchar(32) NOT NULL,
    "token_type" integer NOT NULL,
    "timestamp" integer NOT NULL,
    "is_approved" bool NOT NULL,
    "user_id" integer REFERENCES "auth_user" ("id"),
    "consumer_id" integer NOT NULL REFERENCES "piston_consumer" ("id")
);
CREATE INDEX "piston_consumer_user_id" ON "piston_consumer" ("user_id");
CREATE INDEX "piston_token_user_id" ON "piston_token" ("user_id");
CREATE INDEX "piston_token_consumer_id" ON "piston_token" ("consumer_id");
