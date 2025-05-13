"""
Constants used throughout the TonieToolbox package
"""
SAMPLE_RATE_KHZ: int = 48
ONLY_CONVERT_FRAMEPACKING: int = -1
OTHER_PACKET_NEEDED: int = -2
DO_NOTHING: int = -3
TOO_MANY_SEGMENTS: int = -4
TIMESTAMP_DEDUCT: int = 0x50000000
OPUS_TAGS: list[bytearray] = [
    bytearray(
        b"\x4F\x70\x75\x73\x54\x61\x67\x73\x0D\x00\x00\x00\x4C\x61\x76\x66\x35\x38\x2E\x32\x30\x2E\x31\x30\x30\x03\x00\x00\x00\x26\x00\x00\x00\x65\x6E\x63\x6F\x64\x65\x72\x3D\x6F\x70\x75\x73\x65\x6E\x63\x20\x66\x72\x6F\x6D\x20\x6F\x70\x75\x73\x2D\x74\x6F\x6F\x6C\x73\x20\x30\x2E\x31\x2E\x31\x30\x2A\x00\x00\x00\x65\x6E\x63\x6F\x64\x65\x72\x5F\x6F\x70\x74\x69\x6F\x6E\x73\x3D\x2D\x2D\x71\x75\x69\x65\x74\x20\x2D\x2D\x62\x69\x74\x72\x61\x74\x65\x20\x39\x36\x20\x2D\x2D\x76\x62\x72\x3B\x01\x00\x00\x70\x61\x64\x3D\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30"),
    bytearray(
        b"\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30\x30")
]

# Mapping of language tags to ISO codes
LANGUAGE_MAPPING: dict[str, str] = {
    # Common language names to ISO codes
    'deutsch': 'de-de',
    'german': 'de-de',
    'english': 'en-us',
    'englisch': 'en-us',
    'français': 'fr-fr',
    'french': 'fr-fr',
    'franzosisch': 'fr-fr',
    'italiano': 'it-it',
    'italian': 'it-it',
    'italienisch': 'it-it',
    'español': 'es-es',
    'spanish': 'es-es',
    'spanisch': 'es-es',
    # Two-letter codes
    'de': 'de-de',
    'en': 'en-us',
    'fr': 'fr-fr',
    'it': 'it-it',
    'es': 'es-es',
}

# Mapping of genre tags to tonie categories
GENRE_MAPPING: dict[str, str] = {
    # Standard Tonie category names from tonies.json
    'hörspiel': 'Hörspiele & Hörbücher',
    'hörbuch': 'Hörspiele & Hörbücher',
    'hörbücher': 'Hörspiele & Hörbücher',
    'hörspiele': 'Hörspiele & Hörbücher',
    'audiobook': 'Hörspiele & Hörbücher',
    'audio book': 'Hörspiele & Hörbücher',
    'audio play': 'Hörspiele & Hörbücher',
    'audio-play': 'Hörspiele & Hörbücher',
    'audiospiel': 'Hörspiele & Hörbücher',
    'geschichte': 'Hörspiele & Hörbücher',
    'geschichten': 'Hörspiele & Hörbücher',
    'erzählung': 'Hörspiele & Hörbücher',
    
    # Music related genres
    'musik': 'music',
    'lieder': 'music',
    'songs': 'music',
    'music': 'music',
    'lied': 'music',
    'song': 'music',
    
    # More specific categories
    'kinder': 'Hörspiele & Hörbücher',
    'children': 'Hörspiele & Hörbücher',
    'märchen': 'Hörspiele & Hörbücher',
    'fairy tale': 'Hörspiele & Hörbücher',
    'märche': 'Hörspiele & Hörbücher',
    
    'wissen': 'Wissen & Hörmagazine',
    'knowledge': 'Wissen & Hörmagazine',
    'sachbuch': 'Wissen & Hörmagazine',
    'learning': 'Wissen & Hörmagazine',
    'educational': 'Wissen & Hörmagazine',
    'bildung': 'Wissen & Hörmagazine',
    'information': 'Wissen & Hörmagazine',
    
    'schlaf': 'Schlaflieder & Entspannung',
    'sleep': 'Schlaflieder & Entspannung',
    'meditation': 'Schlaflieder & Entspannung',
    'entspannung': 'Schlaflieder & Entspannung',
    'relaxation': 'Schlaflieder & Entspannung',
    'schlaflied': 'Schlaflieder & Entspannung',
    'einschlafhilfe': 'Schlaflieder & Entspannung',
    
    # Default to standard format for custom
    'custom': 'Hörspiele & Hörbücher',
}

    # Supported file extensions for audio files
SUPPORTED_EXTENSIONS = [
        '.wav', '.mp3', '.aac', '.m4a', '.flac', '.ogg', '.opus',
        '.ape', '.wma', '.aiff', '.mp2', '.mp4', '.webm', '.mka'
    ]

UTI_MAPPINGS = {
            'mp3': 'public.mp3',
            'wav': 'public.wav',
            'flac': 'org.xiph.flac',
            'ogg': 'org.xiph.ogg',
            'opus': 'public.opus',
            'aac': 'public.aac-audio',
            'm4a': 'public.m4a-audio',
            'wma': 'com.microsoft.windows-media-wma',
            'aiff': 'public.aiff-audio',
            'mp2': 'public.mp2',
            'mp4': 'public.mpeg-4-audio',
            'mka': 'public.audio',
            'webm': 'public.webm-audio',
            'ape': 'public.audio',
            'taf': 'public.audio'
        }

ARTWORK_NAMES = [
        'cover', 'folder', 'album', 'front', 'artwork', 'image', 
        'albumart', 'albumartwork', 'booklet'
    ]
ARTWORK_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']


TAG_VALUE_REPLACEMENTS = {
    "Die drei ???": "Die drei Fragezeichen",
    "Die Drei ???": "Die drei Fragezeichen",
    "DIE DREI ???": "Die drei Fragezeichen",
    "Die drei !!!": "Die drei Ausrufezeichen",
    "Die Drei !!!": "Die drei Ausrufezeichen",
    "DIE DREI !!!": "Die drei Ausrufezeichen",
    "TKKG™": "TKKG",
    "Die drei ??? Kids": "Die drei Fragezeichen Kids",
    "Die Drei ??? Kids": "Die drei Fragezeichen Kids",
    "Bibi & Tina": "Bibi und Tina",
    "Benjamin Blümchen™": "Benjamin Blümchen",
    "???": "Fragezeichen",
    "!!!": "Ausrufezeichen",
}

TAG_MAPPINGS = {
    # ID3 (MP3) tags
    'TIT2': 'title',
    'TALB': 'album',
    'TPE1': 'artist',
    'TPE2': 'albumartist',
    'TCOM': 'composer',
    'TRCK': 'tracknumber',
    'TPOS': 'discnumber',
    'TDRC': 'date',
    'TCON': 'genre',
    'TPUB': 'publisher',
    'TCOP': 'copyright',
    'COMM': 'comment',
    
    # Vorbis tags (FLAC, OGG)
    'title': 'title',
    'album': 'album',
    'artist': 'artist',
    'albumartist': 'albumartist',
    'composer': 'composer',
    'tracknumber': 'tracknumber',
    'discnumber': 'discnumber',
    'date': 'date',
    'genre': 'genre',
    'publisher': 'publisher',
    'copyright': 'copyright',
    'comment': 'comment',
    
    # MP4 (M4A, AAC) tags
    '©nam': 'title',
    '©alb': 'album',
    '©ART': 'artist',
    'aART': 'albumartist',
    '©wrt': 'composer',
    'trkn': 'tracknumber',
    'disk': 'discnumber',
    '©day': 'date',
    '©gen': 'genre',
    '©pub': 'publisher',
    'cprt': 'copyright',
    '©cmt': 'comment',
    
    # Additional tags some files might have
    'album_artist': 'albumartist',
    'track': 'tracknumber',
    'track_number': 'tracknumber',
    'disc': 'discnumber',
    'disc_number': 'discnumber',
    'year': 'date',
    'albuminterpret': 'albumartist',  # German tag name
    'interpret': 'artist',            # German tag name

}

CONFIG_TEMPLATE = {
    "metadata": {
        "description": "TonieToolbox configuration",
        "config_version": "1.0"     
    },
    "log_level": "silent", # Options: trace, debug, info, warning, error, critical, silent
    "log_to_file": False, # True if you want to log to a file ~\.tonietoolbox\logs
    "upload": {
        "url": [""], # https://teddycloud.example.com        
        "ignore_ssl_verify": False, # True if you want to ignore SSL certificate verification
        "username": "", # Basic Auth username
        "password": "", # Basic Auth password
        "client_cert_path": "", # Path to client certificate file
        "client_cert_key_path": "" # Path to client certificate key file
    }
}