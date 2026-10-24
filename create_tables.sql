CREATE TABLE IF NOT EXISTS buildings (
    id BIGINT PRIMARY KEY,
    build_year INTEGER,
    building_type_int INTEGER,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    ceiling_height DOUBLE PRECISION,
    flats_count INTEGER,
    floors_total INTEGER,
    has_elevator BOOLEAN
);

CREATE TABLE IF NOT EXISTS flats (
    id BIGINT PRIMARY KEY,
    floor INTEGER,
    is_apartment BOOLEAN,
    kitchen_area DOUBLE PRECISION,
    living_area DOUBLE PRECISION,
    rooms INTEGER,
    studio BOOLEAN,
    total_area DOUBLE PRECISION,
    price NUMERIC(18,2),
    building_id BIGINT
);
