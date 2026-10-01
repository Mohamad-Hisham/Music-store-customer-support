"""Read-only catalog queries for the Chinook database."""

from functools import lru_cache

from ..database import ChinookRepository, get_engine_for_chinook_db


@lru_cache(maxsize=1)
def _repository() -> ChinookRepository:
    return ChinookRepository(get_engine_for_chinook_db())


def get_albums_by_artist(artist: str):
    """Retrieve albums by artist."""
    return _repository().fetch_all(
        """
        SELECT ar.Name AS artist, al.Title AS album
        FROM Artist AS ar
        JOIN Album AS al ON al.ArtistId = ar.ArtistId
        WHERE lower(ar.Name) LIKE lower(:artist)
        ORDER BY al.Title
        """,
        {"artist": f"%{artist.strip()}%"},
    )


def get_tracks_by_artist(artist: str):
    """Retrieve tracks by artist or a partially matching artist name."""
    return _repository().fetch_all(
        """
        SELECT ar.Name AS artist, al.Title AS album, tr.Name AS track
        FROM Artist AS ar
        JOIN Album AS al ON al.ArtistId = ar.ArtistId
        JOIN Track AS tr ON tr.AlbumId = al.AlbumId
        WHERE lower(ar.Name) LIKE lower(:artist)
        ORDER BY al.Title, tr.TrackId
        """,
        {"artist": f"%{artist.strip()}%"},
    )


def get_songs_by_genre(genre: str):
    """Fetch songs matching a genre."""
    return _repository().fetch_all(
        """
        SELECT ge.Name AS genre, tr.Name AS track, ar.Name AS artist,
               al.Title AS album
        FROM Genre AS ge
        JOIN Track AS tr ON tr.GenreId = ge.GenreId
        JOIN Album AS al ON al.AlbumId = tr.AlbumId
        JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
        WHERE lower(ge.Name) LIKE lower(:genre)
        ORDER BY tr.Name
        """,
        {"genre": f"%{genre.strip()}%"},
    )


def check_for_songs(song_title: str):
    """Check whether a song exists by name."""
    return _repository().fetch_all(
        """
        SELECT tr.Name AS track, ar.Name AS artist, al.Title AS album
        FROM Track AS tr
        JOIN Album AS al ON al.AlbumId = tr.AlbumId
        JOIN Artist AS ar ON ar.ArtistId = al.ArtistId
        WHERE lower(tr.Name) LIKE lower(:song_title)
        ORDER BY tr.Name
        """,
        {"song_title": f"%{song_title.strip()}%"},
    )