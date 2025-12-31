-- ============================================================
-- Stremio Remote Files - Database Schema
--
-- Design notes:
-- - Movies and series are stored separately.
-- - Episodes belong to a series.
-- - Files represent physical media files and may map to
--   either a movie OR an episode (never both).
-- - Resolution and size are metadata only; playback URLs
--   are derived at runtime.
-- ============================================================


-- ----------------------------
-- Movies
-- ----------------------------
-- One row per movie (identified by IMDb ID)
CREATE TABLE IF NOT EXISTS movies (
  imdb_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  year INTEGER,
  poster_url TEXT,
  genres TEXT          -- JSON-encoded list
);


-- ----------------------------
-- Series
-- ----------------------------
-- One row per TV series (identified by IMDb ID)
CREATE TABLE IF NOT EXISTS series (
  imdb_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  poster_url TEXT,
  genres TEXT          -- JSON-encoded list
);


-- ----------------------------
-- Episodes
-- ----------------------------
-- One row per episode within a series
-- (season + episode uniquely identify an episode per series)
CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY,
  series_imdb_id TEXT NOT NULL,
  season INTEGER NOT NULL,
  episode INTEGER NOT NULL,
  UNIQUE (series_imdb_id, season, episode),
  FOREIGN KEY (series_imdb_id) REFERENCES series(imdb_id)
);


-- ----------------------------
-- Files (movies OR episodes)
-- ----------------------------
-- Represents a physical media file on disk.
-- A file maps to either:
--   - movie_imdb_id (movie), OR
--   - episode_id (episode)
-- Path is unique and acts as the natural key.
CREATE TABLE IF NOT EXISTS files (
  id INTEGER PRIMARY KEY,
  movie_imdb_id TEXT,
  episode_id INTEGER,
  path TEXT NOT NULL UNIQUE,
  resolution TEXT,
  size INTEGER,
  FOREIGN KEY(movie_imdb_id) REFERENCES movies(imdb_id),
  FOREIGN KEY(episode_id) REFERENCES episodes(id)
);


-- ----------------------------
-- Indexes
-- ----------------------------

-- Fast lookup for movie streams
CREATE INDEX IF NOT EXISTS idx_files_movie
  ON files(movie_imdb_id);

-- Fast lookup for episode streams
CREATE INDEX IF NOT EXISTS idx_files_episode
  ON files(episode_id);

-- Fast episode resolution from Stremio IDs
CREATE INDEX IF NOT EXISTS idx_episodes_lookup
  ON episodes(series_imdb_id, season, episode);
