CREATE TABLE IF NOT EXISTS images (
id SERIAL PRIMARY KEY,
image_url TEXT NOT NULL,
processed BOOLEAN NOT NULL DEFAULT false
);