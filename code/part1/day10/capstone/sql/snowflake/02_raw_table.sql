-- Raw: the file as delivered, all text, plus where each row came from.
-- IF NOT EXISTS, so running this again never wipes the loaded data.
CREATE TABLE IF NOT EXISTS raw_games (
    id             VARCHAR,
    rated          VARCHAR,
    created_at     VARCHAR,
    last_move_at   VARCHAR,
    turns          VARCHAR,
    victory_status VARCHAR,
    winner         VARCHAR,
    increment_code VARCHAR,
    white_id       VARCHAR,
    white_rating   VARCHAR,
    black_id       VARCHAR,
    black_rating   VARCHAR,
    moves          VARCHAR,
    opening_eco    VARCHAR,
    opening_name   VARCHAR,
    opening_ply    VARCHAR,
    source_file    VARCHAR,
    source_line    NUMBER,
    loaded_at      TIMESTAMP_LTZ
);
